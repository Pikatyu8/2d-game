# tests/mutation_harness.py
import os
import sys
import unittest
import shutil

# Ограничиваем графическую подсистему для тестирования
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

TARGET_FILE = "core/physics.py"
BACKUP_FILE = "core/physics.py.bak"

# Список мутаций для внедрения в физический движок
MUTATIONS = [
    {
        "description": "Смена условия перекрытия SAT (>= на <)",
        "original": "return proj1[1] >= proj2[0] and proj2[1] >= proj1[0]",
        "mutated": "return proj1[1] < proj2[0] and proj2[1] >= proj1[0]"
    },
    {
        "description": "Инверсия гравитационного смещения по Y (+ на -)",
        "original": "rect.y += vy",
        "mutated": "rect.y -= vy"
    },
    {
        "description": "Сломанный расчет смещения по оси X",
        "original": "rect.x += vx",
        "mutated": "rect.x += vx * 0"
    }
]

def run_physics_tests():
    """Запускает тесты физики и возвращает True, если все тесты прошли успешно."""
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir="tests", pattern="test_physics.py")
    runner = unittest.TextTestRunner(stream=open(os.devnull, 'w')) # Тихий вывод результатов
    result = runner.run(suite)
    return result.wasSuccessful()

def run_mutation_testing():
    print("=" * 60)
    print("ЗАПУСК МУТАЦИОННОГО ТЕСТИРОВАНИЯ ФИЗИЧЕСКОГО ДВИЖКА")
    print("=" * 60)
    
    if not os.path.exists(TARGET_FILE):
        print(f"Ошибка: Не найден целевой файл {TARGET_FILE}")
        return

    # Создаем резервную копию оригинальной физики
    shutil.copyfile(TARGET_FILE, BACKUP_FILE)
    
    mutants_killed = 0
    mutants_survived = 0
    
    try:
        # 1. Проверяем работоспособность тестов на чистом коде
        print("[Шаг 1] Проверка тестов на оригинальном (чистом) коде...")
        if not run_physics_tests():
            print("[Ошибка] Тесты физики падают даже на оригинальном коде. Исправьте тесты перед мутацией.")
            return
        print("[ОК] Оригинальный код успешно проходит все тесты.")
        print("-" * 60)

        # 2. Внедрение мутаций по очереди
        for idx, mut in enumerate(MUTATIONS, start=1):
            print(f"Мутант #{idx}: {mut['description']}")
            
            # Читаем оригинальный файл
            with open(TARGET_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            
            if mut["original"] not in content:
                print("  [Пропущено] Строка для мутации не найдена в кодовой базе.")
                continue
                
            # Применяем мутацию
            mutated_content = content.replace(mut["original"], mut["mutated"])
            with open(TARGET_FILE, "w", encoding="utf-8") as f:
                f.write(mutated_content)
                
            # Очищаем кэш импорта Python, чтобы изменения в физике применились при следующем вызове тестов
            if "core.physics" in sys.modules:
                del sys.modules["core.physics"]
                
            # Запускаем тесты на мутированном коде
            tests_passed = run_physics_tests()
            
            if not tests_passed:
                print("  [УБИТ] Тесты упали. Ошибка в коде успешно обнаружена тестовым набором.")
                mutants_killed += 1
            else:
                print("  [ВЫЖИЛ] Тесты прошли! Тестовый набор пропустил внедренный критический баг.")
                mutants_survived += 1
                
            # Восстанавливаем файл для следующего шага
            shutil.copyfile(BACKUP_FILE, TARGET_FILE)
            print("-" * 60)

    finally:
        # Обязательно восстанавливаем оригинальный код в случае любых сбоев во время выполнения
        if os.path.exists(BACKUP_FILE):
            shutil.copyfile(BACKUP_FILE, TARGET_FILE)
            os.remove(BACKUP_FILE)
            
    # Вывод результирующей статистики
    total_mutants = mutants_killed + mutants_survived
    score = (mutants_killed / total_mutants * 100) if total_mutants > 0 else 0
    
    print("\n" + "=" * 60)
    print("ИТОГИ МУТАЦИОННОГО АНАЛИЗА")
    print("=" * 60)
    print(f"Всего мутантов создано: {total_mutants}")
    print(f"Мутантов убито (Killed):  {mutants_killed}")
    print(f"Мутантов выжило (Survived): {mutants_survived}")
    print(f"Индекс покрытия мутаций:   {score:.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    run_mutation_testing()