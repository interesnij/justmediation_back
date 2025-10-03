#Different project-related files

##`firestore-rules`

Файл с правилами, связанными с Firestore для приложения, он ограничивает разрешения для
клиентских пользователей (с пользовательским токеном JWT из бэкенда) в отдельных ветвях:

1. Только участники чата (клиент или адвокат) могут получать, создавать, обновлять и
   удалять информацию о чате и внутреннюю коллекцию сообщений (`/chats/{chat_id}`)

2. Пользователь может получать только свои собственные чаты или чаты, в которых он участвует в
   сборе статистики пользователей (`/users/{user_id}/chats/{chats_id}`).

3. Пользователь может получить коллекцию сообщений чата (`chats/{chat_id}/messages/{message_id}/`).

Вы можете ознакомиться с рабочим процессом правил здесь:
https://firebase.google.com/docs/firestore/security/get-started

#### Deploy rules

1. Go to Firebase console `https://console.firebase.google.com` and select
   `JustMediation Platform` project.

2. Go to `Database` service, open its `Rules` and copy whole contents of
   `firestore-rules.js` there.

3. `Publish` new changes.

##`web-firebase-snippet.js`

Это фрагмент кода, который позволяет протестировать базовую функциональность Firebase на локальном языке,
например:

- войдите в систему с помощью пользовательского токена JWT
- получать данные о чатах и статистике пользователей
- проверьте разрешения
- и т.д.
