-- ============================================
-- Искра — Схема базы данных TiDB
-- Версия: 0.1 (Этап 1)
-- Дата: 2026-10-04
-- ============================================

-- 1. Пользователи
CREATE TABLE IF NOT EXISTS users (
    id              BIGINT PRIMARY KEY AUTO_RANDOM,
    external_id     VARCHAR(128) UNIQUE,          -- для будущей привязки (Telegram / email / device)
    username        VARCHAR(100),
    role            ENUM('user', 'admin') DEFAULT 'user',
    daily_limit     INT DEFAULT 100,              -- лимит запросов в сутки
    is_unlimited    BOOLEAN DEFAULT FALSE,        -- безлимит (для владельца и выданных)
    requests_today  INT DEFAULT 0,
    last_request_date DATE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_external_id (external_id),
    INDEX idx_role (role)
);

-- 2. Чаты
CREATE TABLE IF NOT EXISTS chats (
    id              BIGINT PRIMARY KEY AUTO_RANDOM,
    user_id         BIGINT NOT NULL,
    title           VARCHAR(255) DEFAULT 'Новый чат',
    type            ENUM('normal', 'training', 'admin') DEFAULT 'normal',
    is_archived     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_type (type)
);

-- 3. Сообщения
CREATE TABLE IF NOT EXISTS messages (
    id              BIGINT PRIMARY KEY AUTO_RANDOM,
    chat_id         BIGINT NOT NULL,
    role            ENUM('user', 'assistant', 'system') NOT NULL,
    content         LONGTEXT NOT NULL,
    tokens_used     INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE,
    INDEX idx_chat_id (chat_id),
    INDEX idx_created_at (created_at)
);

-- 4. Проекты (готовые папки)
CREATE TABLE IF NOT EXISTS projects (
    id              BIGINT PRIMARY KEY AUTO_RANDOM,
    user_id         BIGINT NOT NULL,
    chat_id         BIGINT,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    status          ENUM('draft', 'in_progress', 'ready', 'archived') DEFAULT 'draft',
    file_path       VARCHAR(512),                 -- путь к zip или папке
    file_size       BIGINT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
);

-- 5. Долгосрочная память агента
CREATE TABLE IF NOT EXISTS agent_memory (
    id              BIGINT PRIMARY KEY AUTO_RANDOM,
    memory_key      VARCHAR(255) NOT NULL,
    memory_value    LONGTEXT NOT NULL,
    memory_type     ENUM('fact', 'preference', 'skill', 'style', 'other') DEFAULT 'fact',
    importance      INT DEFAULT 5,               -- 1-10
    source          VARCHAR(100),                -- откуда пришло (training chat / auto и т.д.)
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_memory_key (memory_key),
    INDEX idx_type (memory_type),
    INDEX idx_importance (importance)
);

-- 6. Логи обучения и автономных отчётов
CREATE TABLE IF NOT EXISTS learning_logs (
    id              BIGINT PRIMARY KEY AUTO_RANDOM,
    period_type     ENUM('day', 'week', 'month', 'year') NOT NULL,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    content         LONGTEXT NOT NULL,           -- текст отчёта
    is_sent         BOOLEAN DEFAULT FALSE,       -- отправлен ли пользователю
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_period (period_type, period_start)
);

-- 7. Действия админа
CREATE TABLE IF NOT EXISTS admin_actions (
    id              BIGINT PRIMARY KEY AUTO_RANDOM,
    admin_user_id   BIGINT NOT NULL,
    action_type     VARCHAR(100) NOT NULL,       -- grant_unlimited, change_limit, etc.
    target_user_id  BIGINT,
    details         JSON,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_user_id) REFERENCES users(id),
    INDEX idx_admin (admin_user_id)
);

-- ============================================
-- Начальные данные
-- ============================================

-- Создаём владельца (тебя) с безлимитом
-- external_id пока ставим 'owner' — потом заменим
INSERT INTO users (external_id, username, role, daily_limit, is_unlimited)
VALUES ('owner', 'Owner', 'admin', 999999, TRUE)
ON DUPLICATE KEY UPDATE is_unlimited = TRUE, role = 'admin';
