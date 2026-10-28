from pyfedappwrap.engine.runtime import FedDBEngine

from app import DateTransformer

engine = FedDBEngine()
engine.register_transformer(DateTransformer())

if __name__ == '__main__':
    engine.start()
    engine.wait_until_stop()