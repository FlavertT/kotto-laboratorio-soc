BEGIN;
--
-- Create model Refrigerator
--
CREATE TABLE "soc_refrigerator" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL, "code" varchar(50) NOT NULL UNIQUE, "location" varchar(200) NOT NULL, "active" bool NOT NULL);
--
-- Create model ParameterChange
--
CREATE TABLE "soc_parameterchange" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "occurred_at" datetime NOT NULL, "parameter" varchar(30) NOT NULL, "previous_value" decimal NOT NULL, "new_value" decimal NOT NULL, "session" varchar(200) NOT NULL, "authorization" varchar(15) NOT NULL, "recorded_at" datetime NOT NULL, "notes" text NOT NULL, "recorded_by_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "refrigerator_id" bigint NOT NULL REFERENCES "soc_refrigerator" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Measurement
--
CREATE TABLE "soc_measurement" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "occurred_at" datetime NOT NULL, "temperature" decimal NOT NULL, "setpoint" decimal NOT NULL, "defrost_active" bool NOT NULL, "refrigerator_id" bigint NOT NULL REFERENCES "soc_refrigerator" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "soc_parameterchange_recorded_by_id_ee5a2d4b" ON "soc_parameterchange" ("recorded_by_id");
CREATE INDEX "soc_parameterchange_refrigerator_id_ae10a12a" ON "soc_parameterchange" ("refrigerator_id");
CREATE INDEX "soc_paramet_refrige_2e147d_idx" ON "soc_parameterchange" ("refrigerator_id", "occurred_at");
CREATE INDEX "soc_measurement_refrigerator_id_0ca31023" ON "soc_measurement" ("refrigerator_id");
CREATE INDEX "soc_measure_refrige_513326_idx" ON "soc_measurement" ("refrigerator_id", "occurred_at");
COMMIT;
