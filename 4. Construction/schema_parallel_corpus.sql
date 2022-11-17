-- SQLITE Schema: Parallel Corpus

--------- Tabel entitas

CREATE TABLE "tb_teks" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "lang" text NOT NULL,
    "text" text NOT NULL,
    "index" int NOT NULL
);

CREATE TABLE "tb_token" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "lang" text NOT NULL,
    "text" text NOT NULL,
    "index" int NOT NULL
);

CREATE TABLE "tb_teks_token" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "teks_id" int NOT NULL,
    "token_id" int NOT NULL,
    "index" int NOT NULL,
    UNIQUE(teks_id, token_id, "index"),
    FOREIGN KEY(teks_id) REFERENCES tb_teks(id),
    FOREIGN KEY(token_id) REFERENCES tb_token(id)
);

CREATE TABLE "tb_teks_token_neighbour" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "teks_id" int NOT NULL,
    "token_id" int NOT NULL,
    "token_id_neighbour" int NOT NULL,
    "distance" int NOT NULL,
    FOREIGN KEY(teks_id) REFERENCES tb_teks(id),
    FOREIGN KEY(token_id) REFERENCES tb_token(id),
    FOREIGN KEY(token_id_neighbour) REFERENCES tb_token(id)
);

---------- View untuk koreksi dan statistik data

-- Perbandingan pasangan teks bahasa Madura dan Indonesia
CREATE VIEW "teks_compare" AS
    SELECT MAD."index", MAD."text" as "text_MAD", IND."text" as "text_IND" FROM
    (SELECT "text", "index" FROM "tb_teks" WHERE "lang" = 'MAD') AS MAD,
    (SELECT "text", "index" FROM "tb_teks" WHERE "lang" = 'IND') AS IND
    WHERE MAD."index" = IND."index";

-- Pratinjau hasil tokenisasi dari teks
CREATE VIEW "teks_token_compare" AS
    SELECT t."index", t.lang, t."text", group_concat(t2."text") FROM tb_teks t, tb_teks_token tt, tb_token t2
    WHERE t.id = tt.teks_id AND tt.token_id = t2.id GROUP BY t.id;

-- Jumlah penggunaan token dari semua teks
CREATE VIEW "token_count" AS
    SELECT t.*, COUNT(*) as  "count" FROM tb_token t, tb_teks_token tt
    WHERE t.id = tt.token_id GROUP BY t.id;

