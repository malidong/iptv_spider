from iptv_spider.logger import logger
from iptv_spider.main import arg_parser, main
from iptv_spider.utils import load_config

if __name__ == "__main__":
    # Parse command-line arguments
    args = arg_parser()
    config = load_config()
    config.update(args.__dict__)

    # Run the main program with provided arguments
    logger.info("Starting IPTV Spider...")
    stats = main(
        m3u_url=config.get("url_or_path"),
        regex_filter=config.get("filter"),
        output_dir=config.get("output_dir"),
        speed_threshold_mb=config.get("speed_threshold_mb", 0.3),
        speed_limit_mb=config.get("speed_limit_mb", 2),
        max_retries=config.get("max_retries", 3),
        request_timeout=config.get("request_timeout", 30)
    )

    # Log statistics
    logger.info("=" * 50)
    logger.info("IPTV Spider Test Summary:")
    logger.info(f"Total channels filtered: {stats['total_channels_filtered']}")
    logger.info(f"Best channels tested: {stats['best_channels_tested']}")
    logger.info(f"Valid channels output: {stats['valid_channels_output']}")
    logger.info(f"Speed threshold: {stats['speed_threshold_mb']} MB/s")
    logger.info(f"Output files: {', '.join(stats['output_files'])}")
    logger.info("=" * 50)
    logger.info("IPTV Spider finished execution.")
