from pathlib import Path
import logging
import multiprocessing as mp
from queue import Empty as QueueEmpty

from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze

logger = logging.getLogger(__name__)

def hijack_models_config():
    """Hijack Magic-PDF models configuration to use v5 det models at runtime."""
    try:
        from magic_pdf.model.sub_modules.ocr.paddleocr2pytorch import pytorch_paddle as pp
    except Exception as exc:
        logger.warning("无法加载PaddleOCR模块以进行运行时修补: %s", exc)
        return

    if getattr(pp, "_hijacked_models_config", False):
        return

    original_get_model_params = pp.get_model_params

    def _get_model_params_hijacked(lang, config):
        det, rec, dict_file = original_get_model_params(lang, config)
        if isinstance(det, str) and det == "ch_PP-OCRv3_det_infer.pth":
            det = "ch_PP-OCRv5_det_infer.pth"
        return det, rec, dict_file

    pp.get_model_params = _get_model_params_hijacked
    pp._hijacked_models_config = True  # type: ignore
    logger.info("已运行时修补OCR检测模型名称为v5 (ch_PP-OCRv3_det_infer.pth -> ch_PP-OCRv5_det_infer.pth)")
 

def _run_pdf_to_md_worker(pdf_path_str: str | Path, output_dir_str: str | Path, result_queue: mp.Queue) -> None:
    """Run PDF->MD in a separate process to avoid UI freezes from long native work."""
    try:
        pdf_path = Path(pdf_path_str)
        output_dir = Path(output_dir_str)

        # 设置输出路径
        paper_name = pdf_path.stem
        output_image_path = output_dir / "images"
        local_image_path = "images"

        # 初始化图片写入器
        image_writer = FileBasedDataWriter(str(output_image_path))
        md_writer = FileBasedDataWriter(str(output_dir))

        # 读取PDF文件
        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(str(pdf_path))  # 读取PDF内容

        # 创建数据集实例
        ds = PymuDocDataset(pdf_bytes)

        # 处理PDF
        logger.info("开始PDF处理流程...")
        hijack_models_config()
        ds.apply(doc_analyze, ocr=True).pipe_ocr_mode(image_writer).dump_md(
            md_writer, f"{paper_name}.md", local_image_path
        )

        markdown_path = output_dir / f"{paper_name}.md"
        result_queue.put({"ok": True, "path": str(markdown_path)})
    except Exception as e:
        result_queue.put({"ok": False, "error": str(e)})

class PDFProcessor:
    """PDF处理器：将PDF转换为Markdown格式"""
    
    def __init__(self):
        """
        初始化PDF处理器
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.debug("初始化PDF处理器")

    def process(self, pdf_path: str | Path, output_dir: str | Path) -> Path:
        """
        处理PDF文件
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录路径

        Returns:
            Path: 生成的Markdown文件路径
        
        Raises:
            FileNotFoundError: 当PDF文件不存在时
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")

        try:
            # 使用子进程执行，避免长时间占用GIL导致UI卡死
            ctx = mp.get_context("spawn")
            result_queue: mp.Queue = ctx.Queue()
            process = ctx.Process(
                target=_run_pdf_to_md_worker,
                args=(str(pdf_path), str(output_dir), result_queue),
                daemon=True,
            )
            process.start()

            result = None
            while True:
                try:
                    result = result_queue.get(timeout=0.2)
                    break
                except QueueEmpty:
                    if not process.is_alive():
                        break

            process.join()

            if not result:
                raise RuntimeError("PDF处理子进程未返回结果")
            if not result.get("ok"):
                raise RuntimeError(result.get("error", "PDF处理失败"))

            markdown_path = Path(result["path"])
            self.logger.info(f"Markdown文件已保存到: {markdown_path}")
            return markdown_path

        except Exception as e:
            self.logger.error(f"PDF处理失败: {str(e)}", exc_info=True)
            raise
