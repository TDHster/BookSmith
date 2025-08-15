# main-test-db.py
from infrastructure.database import init_db, Session
from infrastructure.database.models import User, Book, PlotLine, Chapter

# 🔹 Сначала инициализируем: получаем Session
Session = init_db("sqlite:///storywriter.db")

# 🔹 Теперь создаём сессию
session = Session()

# 🔹 Дальше — как было
user = session.query(User).filter_by(username="author").first()
if not user:
    user = User(username="author", email="author@example.com")
    session.add(user)
    session.commit()

book = Book(
    title="Путешествие мага",
    premise="Молодой маг отправляется в путь, чтобы найти древний артефакт.",
    user_id=user.id
)
session.add(book)
session.commit()

lines = ["Основной сюжет", "Любовная линия", "Антагонист"]
for name in lines:
    line = PlotLine(name=name, book_id=book.id)
    session.add(line)

for i in range(1, 6):
    chapter = Chapter(
        book_id=book.id,
        number=i,
        title=f"Глава {i}",
        generate_flag=(i == 1)
    )
    session.add(chapter)

session.commit()
print("✅ База данных инициализирована: storywriter.db")