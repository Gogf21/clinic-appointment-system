import asyncio
import time
import httpx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')  # Для Windows

BASE_URL = "http://127.0.0.1:8000"

async def create_test_data():
    """Создаёт тестового врача, если его нет"""
    async with httpx.AsyncClient() as client:
        # Проверяем, есть ли врачи
        resp = await client.get(f"{BASE_URL}/doctors/")
        doctors = resp.json()
        
        if not doctors:
            # Создаём врача
            await client.post(f"{BASE_URL}/doctors/", json={
                "full_name": "Тестовый Врач",
                "specialization": "Терапевт",
                "phone": "+79999999999"
            })
            print("✅ Тестовый врач создан")
        else:
            print(f"✅ Врачей в БД: {len(doctors)}")

async def test_generate_slots(duration_minutes: int, work_hours: int = 12):
    """
    Тестирует генерацию слотов.
    duration_minutes - длительность одного слота
    work_hours - продолжительность рабочего дня
    Возвращает: (количество слотов, время генерации мс, время отображения мс)
    """
    async with httpx.AsyncClient() as client:
        # 1. Создаём расписание
        schedule_resp = await client.post(f"{BASE_URL}/schedules/", json={
            "doctor_id": 1,
            "date": "2026-05-14",
            "start_time": f"09:00:00",
            "end_time": f"{9 + work_hours}:00:00"
        })
        
        if schedule_resp.status_code != 200:
            print(f"❌ Ошибка создания расписания: {schedule_resp.text}")
            return 0, 0, 0
        
        schedule = schedule_resp.json()
        schedule_id = schedule["id"]
        
        # 2. Замеряем время генерации слотов
        start_time = time.perf_counter()
        
        gen_resp = await client.post(
            f"{BASE_URL}/schedules/{schedule_id}/generate-slots",
            params={"slot_duration": duration_minutes}
        )
        
        server_time = (time.perf_counter() - start_time) * 1000  # в мс
        
        if gen_resp.status_code != 200:
            print(f"❌ Ошибка генерации слотов: {gen_resp.text}")
            return 0, 0, 0
        
        slots = gen_resp.json()
        num_slots = len(slots)
        
        # 3. Замеряем время получения слотов (имитация отображения)
        start_time = time.perf_counter()
        
        get_resp = await client.get(f"{BASE_URL}/slots/{schedule_id}")
        
        display_time = (time.perf_counter() - start_time) * 1000
        
        # 4. Удаляем расписание (чтобы не засорять БД)
        await client.delete(f"{BASE_URL}/schedules/{schedule_id}")
        
        return num_slots, server_time, display_time

async def main():
    print("=" * 60)
    print("НАГРУЗОЧНОЕ ТЕСТИРОВАНИЕ")
    print("Функция: генерация слотов расписания")
    print("=" * 60)
    
    # Создаём тестовые данные
    await create_test_data()
    
    # Параметры тестирования
    slot_durations = [60, 30, 15, 10, 5]  # длительность слота в минутах
    work_hours = 12  # рабочий день 12 часов
    
    results = []
    
    print("\nЗамеры:")
    print("-" * 60)
    print(f"{'Длит. слота':<15} {'Кол-во слотов':<15} {'Время ген. (мс)':<18} {'Время отобр. (мс)':<20} {'Суммарно (мс)':<15}")
    print("-" * 60)
    
    for duration in slot_durations:
        num_slots, server_time, display_time = await test_generate_slots(duration, work_hours)
        
        total_time = server_time + display_time
        
        results.append({
            "duration": duration,
            "num_slots": num_slots,
            "server_time": server_time,
            "display_time": display_time,
            "total_time": total_time
        })
        
        print(f"{duration} мин{' ':<10} {num_slots:<15} {server_time:<18.2f} {display_time:<20.2f} {total_time:<15.2f}")
    
    # Строим графики
    if results:
        slots_counts = [r["num_slots"] for r in results]
        server_times = [r["server_time"] for r in results]
        display_times = [r["display_time"] for r in results]
        total_times = [r["total_time"] for r in results]
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # График 1: Время генерации
        axes[0].plot(slots_counts, server_times, 'b-o', linewidth=2, markersize=8, label='Время на сервере')
        axes[0].plot(slots_counts, display_times, 'g-s', linewidth=2, markersize=8, label='Время отображения')
        axes[0].plot(slots_counts, total_times, 'r-^', linewidth=2, markersize=8, label='Суммарное время')
        axes[0].set_xlabel('Количество слотов', fontsize=12)
        axes[0].set_ylabel('Время (мс)', fontsize=12)
        axes[0].set_title('Зависимость времени от количества слотов', fontsize=14)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Подписываем точки на графике
        for i, (x, y) in enumerate(zip(slots_counts, total_times)):
            axes[0].annotate(f'{y:.0f} мс', (x, y), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9)
        
        # График 2: Столбчатая диаграмма
        x_pos = range(len(slots_counts))
        width = 0.25
        
        axes[1].bar([p - width for p in x_pos], server_times, width, label='Сервер', color='blue', alpha=0.7)
        axes[1].bar(x_pos, display_times, width, label='Отображение', color='green', alpha=0.7)
        axes[1].bar([p + width for p in x_pos], [s + d for s, d in zip(server_times, display_times)], width, label='Суммарно', color='red', alpha=0.7)
        
        axes[1].set_xlabel('Количество слотов', fontsize=12)
        axes[1].set_ylabel('Время (мс)', fontsize=12)
        axes[1].set_title('Составляющие времени выполнения', fontsize=14)
        axes[1].set_xticks(x_pos)
        axes[1].set_xticklabels(slots_counts)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig('load_test_results.png', dpi=150, bbox_inches='tight')
        print(f"\n✅ График сохранён в файл: load_test_results.png")
        plt.show()
        
        # Вывод таблицы для отчёта
        print("\n" + "=" * 60)
        print("ТАБЛИЦА ДЛЯ ОТЧЁТА:")
        print("=" * 60)
        print(f"{'Длит. слота (мин)':<20} {'Кол-во слотов':<15} {'Время сервера (мс)':<20} {'Время отобр. (мс)':<20} {'Суммарно (мс)':<15}")
        print("-" * 90)
        for r in results:
            print(f"{r['duration']:<20} {r['num_slots']:<15} {r['server_time']:<20.2f} {r['display_time']:<20.2f} {r['total_time']:<15.2f}")

if __name__ == "__main__":
    asyncio.run(main())
