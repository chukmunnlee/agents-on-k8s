import base64, json

REQ, IN, RESP = "/tmp/ks.req", "/tmp/ks.in", "/tmp/ks.resp"

commands = [
  r'''
for i in range(10):
  print(f'{i} ')
  ''',
  r'''
from datetime import datetime
print(f"Current time: {datetime.now()}")
  '''
]

def write_command(filename: str, content: str) -> None:
  with open(filename, 'w') as f:
    f.write(content)
    f.flush()

def read_response() -> str:
  with open(RESP, 'r') as f:
    resp = "".join(f.readlines())
    return base64.b64decode(resp).decode()

for c in commands:
  encoded = base64.b64encode(json.dumps({'code': c}).encode()).decode()
  print(encoded)

  write_command(IN, encoded)
  write_command(REQ, 'GO')

  resp = read_response()
  print('>>> result = ', resp)

