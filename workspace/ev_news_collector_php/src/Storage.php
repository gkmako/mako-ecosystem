<?php

namespace EVNewsCollector;

class Storage
{
    private \PDO $pdo;

    public function __construct(string $dbPath)
    {
        $this->pdo = new \PDO("sqlite:$dbPath");
        $this->pdo->setAttribute(\PDO::ATTR_ERRMODE, \PDO::ERRMODE_EXCEPTION);
        
        $this->pdo->exec('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT UNIQUE,
                summary TEXT,
                published TEXT
            )
        ''');
    }

    public function saveToSQLite(array $articles): void
    {
        $count = 0;
        foreach ($articles as $article) {
            try {
                $stmt = $this->pdo->prepare('''
                    INSERT INTO articles (title, link, summary, published)
                    VALUES (?, ?, ?, ?)
                ''');
                $stmt->execute([
                    $article['title'],
                    $article['link'],
                    $article['summary'],
                    $article['published']
                ]);
                $count++;
            } catch (\PDOException $e) {
                // Пропуск дубликатов
                if ($e->getCode() != 23000) { // SQLITE_CONSTRAINT
                    throw $e;
                }
            }
        }
        
        echo "Сохранено $count статей в SQLite.\n";
    }

    public function exportToCSV(array $articles, string $csvPath): void
    {
        $fp = fopen($csvPath, 'w');
        if (!$fp) {
            throw new \Exception("Не удалось открыть файл для записи CSV: $csvPath");
        }
        
        // Заголовки
        fputcsv($fp, ['title', 'link', 'summary', 'published']);
        
        // Данные
        foreach ($articles as $article) {
            fputcsv($fp, $article);
        }
        
        fclose($fp);
        echo "Экспортировано " . count($articles) . " статей в CSV.\n";
    }

    public function exportToJSON(array $articles, string $jsonPath): void
    {
        file_put_contents($jsonPath, json_encode($articles, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        echo "Экспортировано " . count($articles) . " статей в JSON.\n";
    }
}