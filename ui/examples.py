"""Pre-built example descriptions and schema JSON for quick exploration."""

EXAMPLES = {
    "Company (Lab 1)": {
        "description": (
            "A company database with Employees, Projects, and Departments. "
            "Employees have an SSN (primary key), composite name (first and last), multivalued phone numbers, "
            "derived age, and composite address. Departments have a dno (primary key) and name. "
            "Projects have a pno (primary key) and title. "
            "Employees have Dependents (weak entity) identified by dep_name (partial key). "
            "Employees work on projects with hours worked, and are assigned to departments."
        ),
        "json": """{
  "name": "Company",
  "entities": [
    {
      "name": "Employee",
      "weak": false,
      "attributes": [
        {"name": "ssn", "isPrimaryKey": true},
        {"name": "name", "composite": [{"name": "first"}, {"name": "last"}]},
        {"name": "phones", "isMultiValued": true},
        {"name": "age", "derived": true},
        {"name": "address", "composite": [
          {"name": "street"},
          {"name": "city", "composite": [{"name": "zip"}]}
        ]}
      ]
    },
    {
      "name": "Project",
      "weak": false,
      "attributes": [
        {"name": "pno", "isPrimaryKey": true},
        {"name": "title"}
      ]
    },
    {
      "name": "Department",
      "weak": false,
      "attributes": [
        {"name": "dno", "isPrimaryKey": true},
        {"name": "dname"}
      ]
    },
    {
      "name": "Dependent",
      "weak": true,
      "attributes": [
        {"name": "dep_name", "isPartialKey": true},
        {"name": "gender"}
      ]
    }
  ],
  "relationships": [
    {
      "name": "Works_On",
      "entities": ["Employee", "Project"],
      "cardinalities": ["M", "N"],
      "participations": ["total", "partial"],
      "attributes": [{"name": "hours"}]
    },
    {
      "name": "Has_Dependent",
      "entities": ["Employee", "Dependent"],
      "cardinalities": ["1", "N"],
      "participations": ["partial", "total"],
      "identifying": true
    },
    {
      "name": "Works_For",
      "entities": ["Employee", "Department"],
      "cardinalities": ["N", "1"],
      "participations": ["total", "total"]
    }
  ]
}""",
    },
    "University System": {
        "description": (
            "A university system tracks Students, Instructors, Departments, and Courses. "
            "Students have a student_id, name, and email. Instructors have an instructor_id, name, and rank. "
            "Departments have a dept_code and building. Courses have a course_id, title, and credits. "
            "Students enroll in courses with a grade, and instructors teach courses."
        ),
        "json": """{
  "name": "University",
  "entities": [
    {
      "name": "Student",
      "weak": false,
      "attributes": [
        {"name": "student_id", "isPrimaryKey": true},
        {"name": "name"},
        {"name": "email"}
      ]
    },
    {
      "name": "Instructor",
      "weak": false,
      "attributes": [
        {"name": "instructor_id", "isPrimaryKey": true},
        {"name": "name"},
        {"name": "rank"}
      ]
    },
    {
      "name": "Course",
      "weak": false,
      "attributes": [
        {"name": "course_id", "isPrimaryKey": true},
        {"name": "title"},
        {"name": "credits"}
      ]
    },
    {
      "name": "Department",
      "weak": false,
      "attributes": [
        {"name": "dept_code", "isPrimaryKey": true},
        {"name": "building"}
      ]
    }
  ],
  "relationships": [
    {
      "name": "Enrolls_In",
      "entities": ["Student", "Course"],
      "cardinalities": ["M", "N"],
      "participations": ["total", "partial"],
      "attributes": [{"name": "grade"}]
    },
    {
      "name": "Teaches",
      "entities": ["Instructor", "Course"],
      "cardinalities": ["1", "N"],
      "participations": ["partial", "total"]
    },
    {
      "name": "Belongs_To",
      "entities": ["Instructor", "Department"],
      "cardinalities": ["N", "1"],
      "participations": ["total", "total"]
    }
  ]
}""",
    },
    "Hospital Management": {
        "description": (
            "A hospital management database recording Patients, Doctors, and Wards. "
            "Patients have a patient_id, name, and contact phone. Doctors have a license_no and specialization. "
            "Wards have a ward_no and capacity. "
            "Doctors treat patients with appointment details, and patients are admitted to wards with an admission date."
        ),
        "json": """{
  "name": "Hospital",
  "entities": [
    {
      "name": "Patient",
      "weak": false,
      "attributes": [
        {"name": "patient_id", "isPrimaryKey": true},
        {"name": "name"},
        {"name": "phone", "isMultiValued": true}
      ]
    },
    {
      "name": "Doctor",
      "weak": false,
      "attributes": [
        {"name": "license_no", "isPrimaryKey": true},
        {"name": "name"},
        {"name": "specialization"}
      ]
    },
    {
      "name": "Ward",
      "weak": false,
      "attributes": [
        {"name": "ward_no", "isPrimaryKey": true},
        {"name": "capacity"}
      ]
    }
  ],
  "relationships": [
    {
      "name": "Treats",
      "entities": ["Doctor", "Patient"],
      "cardinalities": ["M", "N"],
      "participations": ["partial", "total"],
      "attributes": [{"name": "diagnosis"}]
    },
    {
      "name": "Admitted_To",
      "entities": ["Patient", "Ward"],
      "cardinalities": ["N", "1"],
      "participations": ["partial", "total"],
      "attributes": [{"name": "admission_date"}]
    }
  ]
}""",
    },
}
