from iptv_spider.logger import logger
from iptv_spider.main import arg_parser, main

if __name__ == "__main__":
    # Parse command-line arguments
    args = arg_parser()

    # Run the main program with provided arguments
    logger.info("Starting IPTV Spider...")
    main(
        m3u_url=args.url_or_path,
        regex_filter=args.filter,
        output_dir=args.output_dir
    )
    logger.info("IPTV Spider finished execution.")
