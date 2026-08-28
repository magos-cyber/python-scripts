# Python Scripts

Utility Python scripts for homelab automation, validation, and monitoring.

## Scripts

### Validation
- `json_validator.py` - Validate and format JSON files
- `yaml_validator.py` - Validate YAML syntax
- `ssl_checker.py` - Check SSL certificate expiration

### Monitoring
- `health_checker.py` - Endpoint health monitoring with alerts
- `metrics_collector.py` - Prometheus-compatible metrics exporter
- `log_aggregator.py` - Multi-source log analysis

### Analysis
- `log_parser.py` - Nginx/Apache log parsing

## Requirements

```bash
pip install requests pyyaml psutil
```

## Usage

```bash
python json_validator.py config.json --format
python health_checker.py
python metrics_collector.py 9101
```

## License

MIT
