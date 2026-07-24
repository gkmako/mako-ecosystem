<?php

namespace EVNewsCollector;

class Deduplicator
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

    public function deduplicate(array $articles): array
    {
        $uniqueArticles = [];
        
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
                $uniqueArticles[] = $article;
            } catch (\PDOException $e) {
                // Дубликат по URL, пропускаем
                if ($e->getCode() != 23000) { // SQLITE_CONSTRAINT
                    throw $e;
                }
            }
        }
        
        echo "Уникальных статей после дедупликации: " . count($uniqueArticles) . "\n";
        return $uniqueArticles;
    }
}