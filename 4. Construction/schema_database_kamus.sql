-- SQLITE Schema

--------- Entities below

-- A glossary index, separated by a new line
CREATE TABLE "tb_kosakata" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "word" text NOT NULL,
    "pronounciation" text, -- Pronunciation
    "homonym_index" int NOT NULL DEFAULT 1
);

-- A contoh index, separated by a dot comma
CREATE TABLE "tb_contoh" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "bahasa" text NOT NULL, -- IND / MAD
    "rawtext" text NOT NULL,
    "index" int NOT NULL -- Index of the contoh in the glossary
);

-- To group equal contoh (as synonym tekss) together
CREATE TABLE "tb_teks" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "text" text NOT NULL, -- the teks
    "context" text, -- konteks (ttg....)
    "alternative" text, -- alternative (kalimat lain)
    "index" int NOT NULL DEFAULT 1
);

-- Explanation for each "ref"
CREATE TABLE "keterangan_kelas_kata" (
    "key" text NOT NULL, -- the key
    "deskripsi" text NOT NULL -- the value
);

-- Explanation for each "ref"
CREATE TABLE "keterangan_kosakata" (
    "key" text NOT NULL, -- the key
    "deskripsi" text NOT NULL
);

CREATE TABLE "keterangan_contoh" (
    "key" text NOT NULL, -- the key
    "deskripsi" text NOT NULL
);

CREATE TABLE "keterangan_teks" (
    "key" text NOT NULL, -- the key
    "deskripsi" text NOT NULL, -- the value
    "kategori" text NOT NULL -- the kategori
);

--------- Relations below

-- kosakata (all) <-- contoh (all)
ALTER TABLE "tb_contoh"
    ADD COLUMN "kosakata_id" int NOT NULL
    REFERENCES tb_kosakata(id);

-- contoh (all) <-- teks (all)
ALTER TABLE "tb_teks"
    ADD COLUMN "contoh_id" int NOT NULL
    REFERENCES tb_contoh(id);

--------- Static information

INSERT INTO "keterangan_kelas_kata" (
    "key",
    "deskripsi"
) VALUES
    ('a', 'Adjektiva'),
    ('Adv', 'Adverbia'),
    ('n', 'Nomina'),
    ('Num', 'Numeralia'),
    ('P', 'Partikel'),
    ('Pron', 'Pronomina'),
    ('Pron persona tunggal', 'Pronomina persona tunggal'),
    ('Pron persona pertama jamak', 'Pronomina persona pertama jamak'),
    ('Pron persona pertama tunggal', 'Pronomina persona pertama tunggal'),
    ('v', 'Verba');

INSERT INTO "keterangan_kosakata" (
    "key",
    "deskripsi"
) VALUES (
    'Ling',
    'Linguistik'
);

INSERT INTO "keterangan_contoh" (
    "key",
    "deskripsi"
) VALUES (
    'Pb',
    'Peribahasa'
),  (
    'Ptn',
    'Pantun'
),  (
    'Krm',
    'Karmina'
),  (
    'Ki',
    'Kiasan'
);

INSERT INTO "keterangan_teks" (
    "key",
    "deskripsi",
    "kategori"
) VALUES (
    'Bkl',
    'Bangkalan',
    'dialek'
),  (
    'Bkl,Pmk',
    'Bangkalan dan Pamekasan',
    'dialek'
),  (
    'Bkl,Smp',
    'Bangkalan dan Sumenep',
    'dialek'
),  (
    'Pmk',
    'Pamekasan',
    'dialek'
),  (
    'Smp',
    'Sumenep',
    'dialek'
),  (
    'Pmk,Smp',
    'Pamekasan dan Sumenep',
    'dialek'
),  (
    'L',
    'Lomra',
    'tingkatan bahasa'
),  (
    'T',
    'Tengngaan',
    'tingkatan bahasa'
),  (
    'A',
    'Alos',
    'tingkatan bahasa'
),  (
    'AT',
    'Alos Tèngghi',
    'tingkatan bahasa'
),  (
    'Ar',
    'Arab',
    'serapan asing'
),  (
    'Bld',
    'Belanda',
    'serapan asing'
),  (
    'Cin',
    'Cina',
    'serapan asing'
),  (
    'Fam',
    'Famili',
    'serapan asing'
),  (
    'Ind',
    'Indonesia',
    'serapan asing'
),  (
    'Ing',
    'Inggris',
    'serapan asing'
),  (
    'Lt',
    'Latin',
    'serapan asing'
),  (
    'Port',
    'Portugis',
    'serapan asing'
),  (
    'Prc',
    'Perancis',
    'serapan asing'
),  (
    'Prsi',
    'Persia',
    'serapan asing'
),  (
    'Tml',
    'Tamil',
    'serapan asing'
),  (
    'Jw',
    'Jawa',
    'serapan daerah'
),  (
    'Skrt',
    'Sansekerta',
    'serapan daerah'
);


ALTER TABLE "tb_kosakata"
    ADD COLUMN "keterangan" text
    REFERENCES keterangan_kosakata(key);

ALTER TABLE "tb_contoh"
    ADD COLUMN "keterangan" text
    REFERENCES keterangan_contoh(key);

ALTER TABLE "tb_teks"
    ADD COLUMN "keterangan" text
    REFERENCES keterangan_teks(key);

ALTER TABLE "tb_teks"
    ADD COLUMN "kelas_kata" text
    REFERENCES keterangan_kelas_kata(key);

--------- Views below

CREATE VIEW "teks_keterangan_count" AS
    SELECT
        keterangan,
        COUNT(*) AS count
    FROM teks
    GROUP BY keterangan;

CREATE VIEW "teks_kelas_kata_count" AS
    SELECT
        kelas_kata,
        COUNT(*) AS count
    FROM teks
    GROUP BY kelas_kata;
