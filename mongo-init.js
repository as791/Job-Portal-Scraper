// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the jobs_db database
db = db.getSiblingDB('jobs_db');

// Create collections
db.createCollection('jobs');
db.createCollection('job_tags');

// Create indexes for better performance
db.jobs.createIndex({ "source": 1, "job_url": 1 }, { unique: true });
db.jobs.createIndex({ "title": "text", "company": "text", "location": "text" });
db.jobs.createIndex({ "posted_date": -1 });
db.jobs.createIndex({ "source": 1 });
db.jobs.createIndex({ "is_remote": 1 });
db.jobs.createIndex({ "tags": 1 });

// Create indexes for job_tags collection
db.job_tags.createIndex({ "name": 1 }, { unique: true });
db.job_tags.createIndex({ "count": -1 });

// Insert some sample tags
db.job_tags.insertMany([
    { name: "python", count: 0, created_at: new Date() },
    { name: "javascript", count: 0, created_at: new Date() },
    { name: "java", count: 0, created_at: new Date() },
    { name: "react", count: 0, created_at: new Date() },
    { name: "nodejs", count: 0, created_at: new Date() },
    { name: "django", count: 0, created_at: new Date() },
    { name: "flask", count: 0, created_at: new Date() },
    { name: "mongodb", count: 0, created_at: new Date() },
    { name: "postgresql", count: 0, created_at: new Date() },
    { name: "aws", count: 0, created_at: new Date() },
    { name: "docker", count: 0, created_at: new Date() },
    { name: "kubernetes", count: 0, created_at: new Date() },
    { name: "remote", count: 0, created_at: new Date() },
    { name: "senior", count: 0, created_at: new Date() },
    { name: "junior", count: 0, created_at: new Date() }
]);

print('MongoDB initialization completed successfully!');
print('Database: jobs_db');
print('Collections: jobs, job_tags');
print('Indexes created for optimal performance');
