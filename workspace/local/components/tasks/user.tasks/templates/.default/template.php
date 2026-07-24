<?php
if (!defined("B_PROLOG_INCLUDED") || B_PROLOG_INCLUDED !== true) die();

if (!empty($arResult["TASKS"])) {
    echo "<h2>Список ваших задач</h2>";
    echo "<ul>";
    foreach ($arResult["TASKS"] as $task) {
        echo "<li>";
        echo "<strong>" . htmlspecialcharsbx($task["TITLE"]) . "</strong><br>";
        echo "Статус: " . htmlspecialcharsbx($task["STATUS"]) . "<br>";
        if (!empty($task["DEADLINE"])) {
            echo "Дедлайн: " . htmlspecialcharsbx($task["DEADLINE"]) . "<br>";
        }
        echo "</li>";
    }
    echo "</ul>";
} else {
    echo "<p>У вас нет активных задач.</p>";
}
?>