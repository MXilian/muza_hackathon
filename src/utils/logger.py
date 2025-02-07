import logging

logger = logging.getLogger(__name__)

# Временный костыль, созданный из-за того, что в консоли сервера отображаются только логи с меткой 'error'
def log(data):
    logger.error(data)

