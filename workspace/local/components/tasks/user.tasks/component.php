<?php
if (!defined("B_PROLOG_INCLUDED") || B_PROLOG_INCLUDED !== true) die();

// Подключаем модуль задач
if (!CModule::IncludeModule("tasks")) {
    ShowError("Модуль задач не установлен.");
    return;
}

// Получаем ID текущего пользователя
$userId = $USER->GetID();

// Параметры фильтрации задач
$arFilter = [
    "RESPONSIBLE_ID" => $userId,
    "STATUS" => [\CTasks::STATE_PENDING, \CTasks::STATE_IN_PROGRESS]
];

// Выборка задач
$arSelect = ["ID", "TITLE", "STATUS", "DEADLINE", "CREATED_DATE"];
$rsTasks = CTasks::GetList([], $arFilter, $arSelect);

$arResult["TASKS"] = [];
while ($task = $rsTasks->Fetch()) {
    $arResult["TASKS"][] = $task;
}

$this->IncludeComponentTemplate();
?>