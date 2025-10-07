# MongoDB Database Schema

## Database: hospital_management

### Collection: users
```javascript
{
  _id: ObjectId,           // Auto-generated MongoDB ID
  email: String,           // User's email (unique)
  name: String,           // User's full name
  phone: String,          // Phone number
  role: String,           // One of: "patient", "staff", "admin"
  password_hash: String,  // Bcrypt hashed password
  is_active: Boolean,     // Account status
  created_at: DateTime,   // Account creation timestamp
}
```

### Collection: tokens
```javascript
{
  _id: ObjectId,           // Auto-generated MongoDB ID
  token_number: String,    // Formatted token number (e.g., "E-001-031025")
  patient_id: String,      // Reference to user._id
  patient_name: String,    // Patient's name
  patient_phone: String,   // Patient's phone
  priority_level: Number,  // 1: Critical, 2: High, 3: Medium-High, 4: Medium-Low, 5: Report, 6: Consultation
  category: String,        // Token category
  status: String,         // "active", "completed", "cancelled"
  symptoms: String,       // Optional symptoms description
  position: Number,       // Current position in queue
  estimated_wait_time: Number, // Estimated wait time in minutes
  created_by: String,     // Reference to user._id who created the token
  created_at: DateTime,   // Token creation timestamp
  updated_at: DateTime    // Last update timestamp
}
```

### Collection: departments
```javascript
{
  _id: ObjectId,          // Auto-generated MongoDB ID
  name: String,          // Department name
  code: String,          // Department code
  head_doctor: String,   // Reference to user._id
  capacity: Number,      // Department capacity
  is_active: Boolean,    // Department status
  created_at: DateTime,  // Creation timestamp
  updated_at: DateTime   // Last update timestamp
}
```

### Collection: appointments
```javascript
{
  _id: ObjectId,          // Auto-generated MongoDB ID
  patient_id: String,     // Reference to user._id
  doctor_id: String,      // Reference to user._id
  department_id: String,  // Reference to departments._id
  token_id: String,       // Reference to tokens._id
  appointment_time: DateTime, // Scheduled time
  status: String,         // "scheduled", "completed", "cancelled"
  notes: String,          // Optional appointment notes
  created_at: DateTime,   // Creation timestamp
  updated_at: DateTime    // Last update timestamp
}
```

### Collection: medical_records
```javascript
{
  _id: ObjectId,          // Auto-generated MongoDB ID
  patient_id: String,     // Reference to user._id
  doctor_id: String,      // Reference to user._id
  appointment_id: String, // Reference to appointments._id
  diagnosis: String,      // Diagnosis details
  prescription: [{        // Array of prescribed medications
    medicine: String,     // Medicine name
    dosage: String,      // Dosage instructions
    duration: String     // Duration of medication
  }],
  notes: String,         // Additional medical notes
  created_at: DateTime,  // Creation timestamp
  updated_at: DateTime   // Last update timestamp
}
```

### Indexes

1. users collection:
   - email (unique)
   - role

2. tokens collection:
   - token_number (unique)
   - patient_id
   - status
   - priority_level
   - created_at

3. appointments collection:
   - patient_id
   - doctor_id
   - appointment_time
   - status

4. medical_records collection:
   - patient_id
   - appointment_id

5. departments collection:
   - code (unique)
   - head_doctor

### Data Validation Rules

1. User roles must be one of: "patient", "staff", "admin"
2. Token status must be one of: "active", "completed", "cancelled"
3. Token priority must be between 1 and 6
4. Appointment status must be one of: "scheduled", "completed", "cancelled"
5. Phone numbers must be valid format
6. Email addresses must be valid format
7. Passwords must be hashed before storage
8. All date fields must be stored in UTC