ALTER TABLE formunculous_fielddefinition 
	  ADD COLUMN multi_select bool NOT NULL DEFAULT False;
-- Comment out if using SQLite as it does not support dropping constraints
ALTER TABLE formunculous_fielddefinition
	  ALTER COLUMN multi_select DROP DEFAULT;

ALTER TABLE formunculous_fielddefinition
	  ADD COLUMN use_radio bool NOT NULL DEFAULT False;
-- Comment out if using SQLite as it does not support dropping constraints
ALTER TABLE formunculous_fielddefinition
	  ALTER COLUMN use_radio DROP DEFAULT;

ALTER TABLE formunculous_applicationdefinition
	  ADD COLUMN authentication_multi_submit bool NOT NULL  DEFAULT False;
-- Comment out if using SQLite as it does not support dropping constraints
ALTER TABLE formunculous_applicationdefinition
	  ALTER COLUMN authentication_multi_submit DROP DEFAULT;

ALTER TABLE formunculous_application
	  ADD COLUMN parent_id integer;

-- Django won't create new m2m tables with a syncdb....
-- http://code.djangoproject.com/ticket/2229

--This is for SQLLite
--CREATE TABLE "formunculous_applicationdefinition_sites" (
--    "id" integer NOT NULL PRIMARY KEY,
--    "applicationdefinition_id" integer NOT NULL REFERENCES "formunculous_applicationdefinition" ("id"),
--    "site_id" integer NOT NULL REFERENCES "django_site" ("id"),
--    UNIQUE ("applicationdefinition_id", "site_id")
--)
--;

--This is for postgresql
CREATE TABLE "formunculous_applicationdefinition_sites" (
    "id" serial NOT NULL PRIMARY KEY,
    "applicationdefinition_id" integer NOT NULL REFERENCES "formunculous_applicationdefinition" ("id") DEFERRABLE INITIALLY DEFERRED,
    "site_id" integer NOT NULL REFERENCES "django_site" ("id") DEFERRABLE INITIALLY DEFERRED,
    UNIQUE ("applicationdefinition_id", "site_id")
)
;
