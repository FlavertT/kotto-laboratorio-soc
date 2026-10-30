BEGIN;
--
-- Create model Experiment
--
CREATE TABLE "soc_experiment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "seed" integer unsigned NOT NULL CHECK ("seed" >= 0), "defense" bool NOT NULL, "started_at" datetime NOT NULL, "case_id" bigint NOT NULL UNIQUE REFERENCES "soc_case" ("id") DEFERRABLE INITIALLY DEFERRED, "refrigerator_id" bigint NOT NULL REFERENCES "soc_refrigerator" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model ControllerEvent
--
CREATE TABLE "soc_controllerevent" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "sequence" integer unsigned NOT NULL CHECK ("sequence" >= 0), "occurred_at" datetime NOT NULL, "kind" varchar(50) NOT NULL, "payload" text NOT NULL CHECK ((JSON_VALID("payload") OR "payload" IS NULL)), "experiment_id" bigint NOT NULL REFERENCES "soc_experiment" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model ResponseAction
--
CREATE TABLE "soc_responseaction" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "occurred_at" datetime NOT NULL, "action" varchar(30) NOT NULL, "success" bool NOT NULL, "details" text NOT NULL CHECK ((JSON_VALID("details") OR "details" IS NULL)), "actor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "event_id" bigint NOT NULL REFERENCES "soc_controllerevent" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create constraint unique_experiment_sequence on model controllerevent
--
CREATE TABLE "new__soc_controllerevent" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "sequence" integer unsigned NOT NULL CHECK ("sequence" >= 0), "occurred_at" datetime NOT NULL, "kind" varchar(50) NOT NULL, "payload" text NOT NULL CHECK ((JSON_VALID("payload") OR "payload" IS NULL)), "experiment_id" bigint NOT NULL REFERENCES "soc_experiment" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_experiment_sequence" UNIQUE ("experiment_id", "sequence"));
INSERT INTO "new__soc_controllerevent" ("id", "sequence", "occurred_at", "kind", "payload", "experiment_id") SELECT "id", "sequence", "occurred_at", "kind", "payload", "experiment_id" FROM "soc_controllerevent";
DROP TABLE "soc_controllerevent";
ALTER TABLE "new__soc_controllerevent" RENAME TO "soc_controllerevent";
CREATE INDEX "soc_experiment_refrigerator_id_d96fcdc9" ON "soc_experiment" ("refrigerator_id");
CREATE INDEX "soc_responseaction_actor_id_5010faec" ON "soc_responseaction" ("actor_id");
CREATE INDEX "soc_responseaction_event_id_07040e1b" ON "soc_responseaction" ("event_id");
CREATE INDEX "soc_controllerevent_experiment_id_c6cff6d8" ON "soc_controllerevent" ("experiment_id");
COMMIT;
