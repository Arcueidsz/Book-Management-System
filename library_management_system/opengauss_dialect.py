from sqlalchemy.dialects.postgresql.psycopg2 import PGDialect_psycopg2
import re

class OpenGaussDialect(PGDialect_psycopg2):
    name = 'opengauss'
    driver = 'psycopg2'

    @classmethod
    def dbapi(cls):
        import psycopg2
        return psycopg2

    def _get_server_version_info(self, connection):
        v = connection.execute("select version()").scalar()
        m = re.match(r'.*openGauss-lite (\d+)\.(\d+)\.(\d+).*', v)
        if not m:
            return (9, 0, 0)  # 默认返回一个兼容的版本
        return tuple(int(x) for x in m.groups()) 