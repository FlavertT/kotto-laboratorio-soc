BEGIN;
--
-- Add field status to experiment
--
CREATE TABLE "new__soc_experiment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "status" varchar(16) NOT NULL, "seed" integer unsigned NOT NULL CHECK ("seed" >= 0), "defense" bool NOT NULL, "started_at" datetime NOT NULL, "case_id" bigint NOT NULL UNIQUE REFERENCES "soc_case" ("id") DEFERRABLE INITIALLY DEFERRED, "refrigerator_id" bigint NOT NULL REFERENCES "soc_refrigerator" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "new__soc_experiment" ("id", "seed", "defense", "started_at", "case_id", "refrigerator_id", "status") SELECT "id", "seed", "defense", "started_at", "case_id", "refrigerator_id", 'running' FROM "soc_experiment";
DROP TABLE "soc_experiment";
ALTER TABLE "new__soc_experiment" RENAME TO "soc_experiment";
CREATE INDEX "soc_experiment_refrigerator_id_d96fcdc9" ON "soc_experiment" ("refrigerator_id");
COMMIT;
