"""Conventional comparison SDK. Domain rules use stdlib SQLite transactions, not RF2."""
import os,sqlite3,stat
class BookingError(Exception):
 def __init__(self,code):self.code=code;super().__init__(str(code))
def _number(n,lo,hi):
 if type(n)is not int or not lo<=n<=hi:raise BookingError(22)
 return n
def _id(s):
 if not isinstance(s,str)or not s.isascii()or not s.isdecimal()or s.startswith('0')or len(s)>20 or int(s)>2**64-1:raise BookingError(22)
 return s
def _regular(path):
 try:s=os.lstat(path)
 except FileNotFoundError:raise BookingError(2)
 if stat.S_ISLNK(s.st_mode):raise BookingError(62)
 if not stat.S_ISREG(s.st_mode)or s.st_nlink!=1:raise BookingError(79)
def execute(path,action,expected=0,id=None,room=0,day=0,start=0,finish=0):
 """init/list/reserve/cancel; ordinal dates and half-open same-day minutes. Raises BookingError."""
 if action not in('init','list','reserve','cancel'):raise BookingError(22)
 if action in('reserve','cancel'):_number(expected,1,2**32-1);_id(id)
 if action=='reserve':
  _number(room,1,16);_number(day,1,3652059);_number(start,0,1439);_number(finish,1,1440)
  if start>=finish:raise BookingError(22)
 created=False;connection=None;committing=False
 try:
  if action=='init':
   try:fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
   except FileExistsError:raise BookingError(17)
   os.close(fd);created=True
  _regular(path)
  connection=sqlite3.connect(path,timeout=0,isolation_level=None)
  connection.execute('PRAGMA synchronous=FULL');connection.execute('PRAGMA journal_mode=DELETE')
  connection.execute('BEGIN'if action=='list'else'BEGIN IMMEDIATE')
  if action=='init':
   connection.execute('CREATE TABLE metadata(revision INTEGER NOT NULL)');connection.execute('INSERT INTO metadata VALUES(1)')
   connection.execute('CREATE TABLE bookings(id TEXT PRIMARY KEY,room INTEGER NOT NULL,day INTEGER NOT NULL,start INTEGER NOT NULL,finish INTEGER NOT NULL)')
  revision=connection.execute('SELECT revision FROM metadata').fetchone()[0]
  rows=[dict(id=r[0],room=r[1],day=r[2],start=r[3],finish=r[4])for r in connection.execute('SELECT id,room,day,start,finish FROM bookings ORDER BY rowid')]
  if action in('reserve','cancel'):
   if revision!=expected:raise BookingError(409)
   found=next((r for r in rows if r['id']==id),None)
   if action=='reserve':
    if found:raise BookingError(17)
    if len(rows)>=256:raise BookingError(27)
    if any(r['room']==room and r['day']==day and start<r['finish']and r['start']<finish for r in rows):raise BookingError(409)
    connection.execute('INSERT INTO bookings VALUES(?,?,?,?,?)',(id,room,day,start,finish));rows.append(dict(id=id,room=room,day=day,start=start,finish=finish))
   else:
    if found is None:raise BookingError(404)
    connection.execute('DELETE FROM bookings WHERE id=?',(id,));rows=[r for r in rows if r['id']!=id]
   revision+=1;connection.execute('UPDATE metadata SET revision=?',(revision,))
  committing=True;connection.commit();committing=False
  return dict(revision=revision,bookings=rows)
 except BookingError:
  if connection:connection.rollback()
  raise
 except sqlite3.OperationalError as e:
  if connection:connection.rollback()
  if 'locked'in str(e)or'busy'in str(e):raise BookingError(35)
  raise BookingError(9002 if committing or created else 5)
 except sqlite3.DatabaseError:raise BookingError(9001)
 except OSError as e:raise BookingError(e.errno or 5)
 finally:
  if connection:connection.close()
