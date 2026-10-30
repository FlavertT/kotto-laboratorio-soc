BEGIN;
--
-- Create model ChangeAuthorization
--
CREATE TABLE "soc_changeauthorization" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "username" varchar(100) NOT NULL, "setpoint" decimal NOT NULL, "defrost_minutes" integer unsigned NOT NULL CHECK ("defrost_minutes" >= 0), "valid_from" datetime NOT NULL, "valid_until" datetime NOT NULL, "created_at" datetime NOT NULL, "approved_by_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "consumed_by_id" bigint NULL UNIQUE REFERENCES "soc_controllerevent" ("id") DEFERRABLE INITIALLY DEFERRED, "experiment_id" bigint NOT NULL REFERENCES "soc_experiment" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "authorization_valid_window" CHECK ("valid_until" > ("valid_from")));
CREATE INDEX "soc_changeauthorization_approved_by_id_0239ec8b" ON "soc_changeauthorization" ("approved_by_id");
CREATE INDEX "soc_changeauthorization_experiment_id_dc1a11eb" ON "soc_changeauthorization" ("experiment_id");
COMMIT;
