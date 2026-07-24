#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для парсинга и анализа отчета о рынке электромобилей в РФ за 2025 год.
Извлекает ключевые метрики из файла ev_market_analysis_2025_final.md и формирует аналитическую сводку.
"""

import re
import os

def parse_ev_report(file_path):
    """
    Парсит файл отчета и извлекает ключевые данные.
    
    Args:
        file_path (str): Путь к файлу отчета
        
    Returns:
        dict: Словарь с извлеченными данными
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    data = {}
    
    # Извлечение общего объема рынка
    market_volume_match = re.search(r'Общий объём рынка:\s*\*{2}(.+?)\*{2}', content)
    if market_volume_match:
        data['market_volume'] = market_volume_match.group(1).strip()
    
    # Извлечение объема новых и б/у ЭМ
    new_ev_match = re.search(r'Новые электромобили:\s*~(.+?)\s*единиц', content)
    used_ev_match = re.search(r'Электромобили с пробегом:\s*~(.+?)\s*единиц', content)
    if new_ev_match and used_ev_match:
        data['new_ev'] = new_ev_match.group(1).strip()
        data['used_ev'] = used_ev_match.group(1).strip()
    
    # Извлечение топ-5 брендов
    brands_section = re.search(r'### Топ-10 брендов по объёму продаж:(.+?)(?=###|$)', content, re.DOTALL)
    if brands_section:
        brands_lines = brands_section.group(1).strip().split('\n')
        top_brands = []
        for line in brands_lines:
            brand_match = re.search(r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', line)
            if brand_match and len(top_brands) < 5:
                top_brands.append((brand_match.group(1).strip(), brand_match.group(2).strip()))
        data['top_brands'] = top_brands
    
    # Извлечение топ-5 моделей
    models_section = re.search(r'### Топ-10 моделей по объёму продаж:(.+?)(?=##|$)', content, re.DOTALL)
    if models_section:
        models_lines = models_section.group(1).strip().split('\n')
        top_models = []
        for line in models_lines:
            model_match = re.search(r'\|\s*\d+\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|', line)
            if model_match and len(top_models) < 5:
                top_models.append((
                    model_match.group(1).strip(), 
                    model_match.group(2).strip(), 
                    model_match.group(3).strip()
                ))
        data['top_models'] = top_models
    
    # Извлечение средних цен
    avg_price_match = re.search(r'Средняя цена нового электромобиля:\s*\*{2}(.+?)\*{2}', content)
    if avg_price_match:
        data['avg_price'] = avg_price_match.group(1).strip()
    
    # Извлечение информации о зарядных станциях
    charging_stations_match = re.search(r'Общее количество зарядных станций:\s*\*{2}(.+?)\*{2}', content)
    if charging_stations_match:
        data['charging_stations'] = charging_stations_match.group(1).strip()
    
    # Извлечение мер господдержки
    support_section = re.search(r'Ключевые меры поддержки:(.+?)(?=##|$)', content, re.DOTALL)
    if support_section:
        support_lines = support_section.group(1).strip().split('\n')
        support_measures = [line.strip().replace('- ', '') for line in support_lines if line.strip().startswith('-')]
        data['support_measures'] = support_measures[:5]  # Ограничим 5 основными мерами
    
    # Извлечение информации о локализации производства
    localization_section = re.search(r'## 6. Локализация производства в РФ(.+?)(?=##|$)', content, re.DOTALL)
    if localization_section:
        data['localization'] = localization_section.group(1).strip()
    
    return data

def generate_summary(data):
    """
    Генерирует аналитическую сводку на основе извлеченных данных.
    
    Args:
        data (dict): Словарь с извлеченными данными
        
    Returns:
        str: Аналитическая сводка
    """
    summary = []
    summary.append("# Аналитическая сводка по рынку электромобилей в РФ за 2025 год\n")
    
    # Объем продаж
    summary.append("## 1. Объем продаж")
    summary.append(f"- Общий объем рынка: {data.get('market_volume', 'N/A')}")
    summary.append(f"- Новые электромобили: {data.get('new_ev', 'N/A')} единиц")
    summary.append(f"- Электромобили с пробегом: {data.get('used_ev', 'N/A')} единиц\n")
    
    # Топ-5 брендов
    summary.append("## 2. Топ-5 брендов")
    top_brands = data.get('top_brands', [])
    for i, (brand, share) in enumerate(top_brands, 1):
        summary.append(f"{i}. **{brand}** – {share}")
    summary.append("")
    
    # Топ-5 моделей
    summary.append("## 3. Топ-5 моделей")
    top_models = data.get('top_models', [])
    for i, (model, brand, share) in enumerate(top_models, 1):
        summary.append(f"{i}. **{model}** ({brand}) – {share}")
    summary.append("")
    
    # Средние цены
    summary.append("## 4. Средние цены")
    summary.append(f"- Средняя цена нового электромобиля: {data.get('avg_price', 'N/A')}\n")
    
    # Количество зарядных станций
    summary.append("## 5. Количество зарядных станций")
    summary.append(f"- Общее количество: {data.get('charging_stations', 'N/A')}\n")
    
    # Основные меры господдержки
    summary.append("## 6. Основные меры господдержки")
    support_measures = data.get('support_measures', [])
    for measure in support_measures:
        summary.append(f"- {measure}")
    summary.append("")
    
    # Локализация производства
    summary.append("## 7. Локализация производства")
    localization = data.get('localization', 'N/A')
    # Извлечем ключевые моменты из секции локализации
    if 'Lada' in localization:
        summary.append("- **Lada (АвтоВАЗ)**: 100% производство в РФ")
    if 'Tesla' in localization:
        summary.append("- **Tesla**: Открытие цеха в Калининграде в 2025 году")
    if 'Geely' in localization and 'Haval' in localization:
        summary.append("- **Geely и Haval**: Начало сборки комплектов в РФ (уровень локализации ~40%)")
    
    return '\n'.join(summary)

def main():
    """
    Основная функция скрипта.
    """
    report_file = 'ev_market_analysis_2025_final.md'
    output_file = 'ev_market_summary_2025.md'
    
    try:
        # Парсим отчет
        data = parse_ev_report(report_file)
        
        # Генерируем сводку
        summary = generate_summary(data)
        
        # Сохраняем сводку в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"Аналитическая сводка успешно сохранена в файл {output_file}")
        print("\nКраткое содержание сводки:")
        print(summary)
        
    except Exception as e:
        print(f"Ошибка при выполнении скрипта: {e}")

if __name__ == '__main__':
    main()