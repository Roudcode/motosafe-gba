import sys
from datetime import datetime, timezone
sys.path.insert(0, 'backend')
import scrapear_noticias_robos as s
class Cursor:
    def execute(self, q, p):
        self.query, self.params = q, p
    def fetchall(self):
        return [(7, 'Robaron una moto en San Martin', -34.57, -58.53, 100)]
c = Cursor()
result = s._detectar_duplicado_semantico(c, 'Robaron una moto en San Martin', 'robo', -34.57, -58.53, 100, datetime(2026, 1, 1, tzinfo=timezone.utc))
print({'duplicate_id': result, 'lower_bound': str(c.params[1]), 'upper_bound_present': ' <= ' in c.query})
