const request = require('supertest');
const { app } = require('../src/server');
const { initDatabase, closeDatabase, getDb } = require('../src/db/database');

// Override database path for testing
process.env.DATABASE_PATH = './data/test_patients.db';

let server;

beforeAll(() => {
  initDatabase();
});

afterAll(() => {
  closeDatabase();
  // Clean up test database
  const fs = require('fs');
  try { fs.unlinkSync('./data/test_patients.db'); } catch (e) {}
  try { fs.unlinkSync('./data/test_patients.db-wal'); } catch (e) {}
  try { fs.unlinkSync('./data/test_patients.db-shm'); } catch (e) {}
});

const validPatient = {
  first_name: 'John',
  last_name: 'Smith',
  date_of_birth: '1990-05-15',
  sex: 'Male',
  phone_number: '5551234567',
  email: 'john.smith@test.com',
  address_line_1: '789 Test Street',
  address_line_2: 'Suite 100',
  city: 'Dallas',
  state: 'TX',
  zip_code: '75201',
  insurance_provider: 'UnitedHealth',
  insurance_member_id: 'UH-999888',
  preferred_language: 'English',
  emergency_contact_name: 'Jane Smith',
  emergency_contact_phone: '5559876543',
};

describe('Patient API', () => {
  let createdPatientId;

  // ─── POST /patients ────────────────────────────────────────────────────────
  describe('POST /patients', () => {
    it('should create a new patient with valid data', async () => {
      const res = await request(app)
        .post('/patients')
        .send(validPatient)
        .expect(201);

      expect(res.body).toHaveProperty('patient_id');
      expect(res.body.first_name).toBe('John');
      expect(res.body.last_name).toBe('Smith');
      expect(res.body.date_of_birth).toBe('1990-05-15');
      expect(res.body.sex).toBe('Male');
      expect(res.body.phone_number).toBe('5551234567');
      expect(res.body.city).toBe('Dallas');
      expect(res.body.state).toBe('TX');
      createdPatientId = res.body.patient_id;
    });

    it('should reject patient with missing required fields', async () => {
      const res = await request(app)
        .post('/patients')
        .send({ first_name: 'John' })
        .expect(400);

      expect(res.body).toHaveProperty('error', 'Validation failed');
      expect(res.body.details.length).toBeGreaterThan(0);
    });

    it('should reject patient with future date of birth', async () => {
      const res = await request(app)
        .post('/patients')
        .send({ ...validPatient, date_of_birth: '2099-01-01' })
        .expect(400);

      expect(res.body.details.some(d => d.field === 'date_of_birth')).toBe(true);
    });

    it('should reject patient with invalid phone number', async () => {
      const res = await request(app)
        .post('/patients')
        .send({ ...validPatient, phone_number: '123' })
        .expect(400);

      expect(res.body.details.some(d => d.field === 'phone_number')).toBe(true);
    });

    it('should reject patient with invalid state abbreviation', async () => {
      const res = await request(app)
        .post('/patients')
        .send({ ...validPatient, state: 'XX' })
        .expect(400);

      expect(res.body.details.some(d => d.field === 'state')).toBe(true);
    });

    it('should reject patient with invalid zip code', async () => {
      const res = await request(app)
        .post('/patients')
        .send({ ...validPatient, zip_code: '123' })
        .expect(400);

      expect(res.body.details.some(d => d.field === 'zip_code')).toBe(true);
    });

    it('should reject patient with invalid sex value', async () => {
      const res = await request(app)
        .post('/patients')
        .send({ ...validPatient, sex: 'InvalidValue' })
        .expect(400);

      expect(res.body.details.some(d => d.field === 'sex')).toBe(true);
    });

    it('should accept patient with ZIP+4 format', async () => {
      const res = await request(app)
        .post('/patients')
        .send({ ...validPatient, zip_code: '75201-1234', phone_number: '5550001111' })
        .expect(201);

      expect(res.body.zip_code).toBe('75201-1234');
    });
  });

  // ─── GET /patients ─────────────────────────────────────────────────────────
  describe('GET /patients', () => {
    it('should list all patients', async () => {
      const res = await request(app)
        .get('/patients')
        .expect(200);

      expect(res.body).toHaveProperty('patients');
      expect(res.body).toHaveProperty('total');
      expect(res.body.patients.length).toBeGreaterThan(0);
    });

    it('should filter patients by last_name', async () => {
      const res = await request(app)
        .get('/patients?last_name=Smith')
        .expect(200);

      expect(res.body.patients.every(p => p.last_name === 'Smith')).toBe(true);
    });

    it('should filter patients by phone_number', async () => {
      const res = await request(app)
        .get('/patients?phone_number=5551234567')
        .expect(200);

      expect(res.body.patients.length).toBeGreaterThan(0);
    });

    it('should return empty results for non-existent filter', async () => {
      const res = await request(app)
        .get('/patients?last_name=NonExistentName')
        .expect(200);

      expect(res.body.patients.length).toBe(0);
    });
  });

  // ─── GET /patients/:id ─────────────────────────────────────────────────────
  describe('GET /patients/:id', () => {
    it('should return a patient by ID', async () => {
      const res = await request(app)
        .get(`/patients/${createdPatientId}`)
        .expect(200);

      expect(res.body.patient_id).toBe(createdPatientId);
      expect(res.body.first_name).toBe('John');
    });

    it('should return 404 for non-existent patient', async () => {
      await request(app)
        .get('/patients/00000000-0000-0000-0000-000000000000')
        .expect(404);
    });

    it('should return 400 for invalid UUID', async () => {
      await request(app)
        .get('/patients/not-a-uuid')
        .expect(400);
    });
  });

  // ─── PUT /patients/:id ─────────────────────────────────────────────────────
  describe('PUT /patients/:id', () => {
    it('should update a patient partially', async () => {
      const res = await request(app)
        .put(`/patients/${createdPatientId}`)
        .send({ first_name: 'Jonathan', email: 'jonathan.smith@test.com' })
        .expect(200);

      expect(res.body.first_name).toBe('Jonathan');
      expect(res.body.email).toBe('jonathan.smith@test.com');
      expect(res.body.last_name).toBe('Smith'); // unchanged
    });

    it('should return 404 for non-existent patient', async () => {
      await request(app)
        .put('/patients/00000000-0000-0000-0000-000000000000')
        .send({ first_name: 'Test' })
        .expect(404);
    });
  });

  // ─── DELETE /patients/:id ──────────────────────────────────────────────────
  describe('DELETE /patients/:id', () => {
    it('should soft-delete a patient', async () => {
      const res = await request(app)
        .delete(`/patients/${createdPatientId}`)
        .expect(200);

      expect(res.body.patient).toHaveProperty('deleted_at');
      expect(res.body.patient.deleted_at).not.toBeNull();
    });

    it('should not find a soft-deleted patient via GET', async () => {
      await request(app)
        .get(`/patients/${createdPatientId}`)
        .expect(404);
    });

    it('should not include soft-deleted patients in list', async () => {
      const res = await request(app)
        .get('/patients')
        .expect(200);

      const found = res.body.patients.find(p => p.patient_id === createdPatientId);
      expect(found).toBeUndefined();
    });
  });

  // ─── Health Check ──────────────────────────────────────────────────────────
  describe('GET /health', () => {
    it('should return healthy status', async () => {
      const res = await request(app)
        .get('/health')
        .expect(200);

      expect(res.body.status).toBe('healthy');
      expect(res.body).toHaveProperty('timestamp');
      expect(res.body).toHaveProperty('uptime');
    });
  });
});
