"""Entry point for the campaign logger application."""

if __name__ == "__main__":  # pragma: no cover
    from campaign_logger.cli import main

    main(obj={}, standalone_mode=False)  # pylint: disable=no-value-for-parameter
