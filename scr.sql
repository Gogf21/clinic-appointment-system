
CREATE DATABASE clinic_appointment_db;


\c clinic_appointment_db;


CREATE TABLE Doctor (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(50) NOT NULL,
    phone VARCHAR(20)
);


CREATE TABLE Patient (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(50)
);


CREATE TABLE Service (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    duration INTEGER NOT NULL,
    specialization VARCHAR(50) NOT NULL
);


CREATE TABLE Schedule (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    FOREIGN KEY (doctor_id) REFERENCES Doctor(id) ON DELETE CASCADE,
    CONSTRAINT check_time CHECK (start_time < end_time)
);


CREATE TABLE Slot (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    appointment_id INTEGER NULL,
    FOREIGN KEY (schedule_id) REFERENCES Schedule(id) ON DELETE CASCADE,
    CONSTRAINT check_slot_time CHECK (start_time < end_time)
);


CREATE TABLE Appointment (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES Patient(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES Doctor(id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES Service(id) ON DELETE CASCADE,
    FOREIGN KEY (slot_id) REFERENCES Slot(id) ON DELETE CASCADE,
    CONSTRAINT check_status CHECK (status IN ('scheduled', 'confirmed', 'in_progress', 'completed', 'cancelled', 'no_show'))
);

-- Добавление внешнего ключа appointment_id в таблицу Slot после создания Appointment
ALTER TABLE Slot ADD CONSTRAINT fk_slot_appointment FOREIGN KEY (appointment_id) REFERENCES Appointment(id) ON DELETE SET NULL;

-- Создание индексов для повышения производительности
CREATE INDEX idx_appointment_patient ON Appointment(patient_id);
CREATE INDEX idx_appointment_doctor ON Appointment(doctor_id);
CREATE INDEX idx_appointment_date ON Appointment(created_at);
CREATE INDEX idx_slot_schedule ON Slot(schedule_id);
CREATE INDEX idx_slot_booked ON Slot(is_booked);
CREATE INDEX idx_schedule_doctor ON Schedule(doctor_id);
CREATE INDEX idx_schedule_date ON Schedule(date);
