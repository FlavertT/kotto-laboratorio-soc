BEGIN;
--
-- Create model Case
--
CREATE TABLE "soc_case" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(200) NOT NULL, "description" text NOT NULL, "status" varchar(20) NOT NULL, "created_at" datetime NOT NULL);
--
-- Create model Alert
--
CREATE TABLE "soc_alert" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "occurred_at" datetime NOT NULL, "rule" varchar(100) NOT NULL, "details" text NOT NULL CHECK ((JSON_VALID("details") OR "details" IS NULL)), "case_id" bigint NOT NULL REFERENCES "soc_case" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model Evidence
--
CREATE TABLE "soc_evidence" ("id" char(32) NOT NULL PRIMARY KEY, "original_name" varchar(255) NOT NULL, "file" varchar(100) NOT NULL, "sha256" varchar(64) NOT NULL, "size" bigint unsigned NOT NULL CHECK ("size" >= 0), "source" varchar(255) NOT NULL, "collected_at" datetime NOT NULL, "ingested_at" datetime NOT NULL, "case_id" bigint NOT NULL REFERENCES "soc_case" ("id") DEFERRABLE INITIALLY DEFERRED, "collected_by_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model CustodyEvent
--
CREATE TABLE "soc_custodyevent" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "recorded_at" datetime NOT NULL, "action" varchar(100) NOT NULL, "recipient" varchar(200) NOT NULL, "notes" text NOT NULL, "actor_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "evidence_id" char(32) NOT NULL REFERENCES "soc_evidence" ("id") DEFERRABLE INITIALLY DEFERRED);
--
-- Create model TimelineEvent
--
CREATE TABLE "soc_timelineevent" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "occurred_at" datetime NOT NULL, "category" varchar(50) NOT NULL, "description" text NOT NULL, "case_id" bigint NOT NULL REFERENCES "soc_case" ("id") DEFERRABLE INITIALLY DEFERRED, "evidence_id" char(32) NULL REFERENCES "soc_evidence" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE INDEX "soc_alert_case_id_2618876c" ON "soc_alert" ("case_id");
CREATE INDEX "soc_evidence_case_id_8a53a3a3" ON "soc_evidence" ("case_id");
CREATE INDEX "soc_evidence_collected_by_id_60ec1312" ON "soc_evidence" ("collected_by_id");
CREATE INDEX "soc_custodyevent_actor_id_b295bc56" ON "soc_custodyevent" ("actor_id");
CREATE INDEX "soc_custodyevent_evidence_id_791b5bec" ON "soc_custodyevent" ("evidence_id");
CREATE INDEX "soc_timelineevent_case_id_89801d8a" ON "soc_timelineevent" ("case_id");
CREATE INDEX "soc_timelineevent_evidence_id_98f64ebb" ON "soc_timelineevent" ("evidence_id");
COMMIT;
