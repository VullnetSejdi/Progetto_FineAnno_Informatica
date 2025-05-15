```mermaid
erDiagram
    User {
        int id PK
        string email
        string password_hash
        string name
        string phone
        boolean verified
        datetime created_at
    }
    Verification_token {
        int id PK
        int user_id FK
        string token
        datetime expires_at
    }
    Password_reset {
        int id PK
        int user_id FK
        string token
        datetime expires_at
    }
    Service {
        int id PK
        string name
        string description
        string image_url
    }
    Request {
        int id PK
        int user_id FK
        string type
        text details
        datetime created_at
        string status
    }
    Request_service {
        int request_id FK
        int service_id FK
    }
    Chat_history {
        int id PK
        int user_id FK
        string message
        string response
        datetime timestamp
    }

    User ||--o{ Verification_token : "has"
    User ||--o{ Password_reset : "has"
    User ||--o{ Request : "makes"
    User ||--o{ Chat_history : "generates"
    Request ||--o{ Request_service : "includes"
    Service ||--o{ Request_service : "belongs to"