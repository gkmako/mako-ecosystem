<?php

namespace EVNewsCollector;

use GuzzleHttp\Client;
use GuzzleHttp\Promise;
use Symfony\Component\Yaml\Yaml;

class Collector
{
    private Client $client;
    private array $config;

    public function __construct(string $configPath)
    {
        $this->client = new Client();
        $this->config = Yaml::parseFile($configPath);
    }

    public function collectNews(): array
    {
        $sources = $this->config['sources'] ?? [];
        $keywords = $this->config['keywords'] ?? [];
        
        $articles = [];
        
        foreach ($sources as $source) {
            try {
                $response = $this->client->get($source);
                $xml = simplexml_load_string($response->getBody()->getContents());
                
                foreach ($xml->channel->item as $item) {
                    $title = (string) $item->title;
                    $description = (string) $item->description;
                    $content = strtolower($title . ' ' . $description);
                    
                    foreach ($keywords as $keyword) {
                        if (strpos($content, strtolower($keyword)) !== false) {
                            $articles[] = [
                                'title' => $title,
                                'link' => (string) $item->link,
                                'summary' => $description,
                                'published' => (string) $item->pubDate
                            ];
                            break;
                        }
                    }
                }
            } catch (\Exception $e) {
                error_log("Error fetching $source: " . $e->getMessage());
            }
        }
        
        echo "Собрано " . count($articles) . " статей.\n";
        return $articles;
    }
}