-- SQLITE Schema: Database Kamus

--------- Tabel entitas

CREATE TABLE "tb_kosakata" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "word" text NOT NULL,
    "pronounciation" text,
    "homonym_index" int NOT NULL DEFAULT 1
);

CREATE TABLE "tb_contoh" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "bahasa" text NOT NULL,
    "rawtext" text NOT NULL,
    "index" int NOT NULL
);

CREATE TABLE "tb_teks" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "text" text NOT NULL,
    "context" text,
    "alternative" text,
    "index" int NOT NULL DEFAULT 1
);

--------- Tabel daftar keterangan

CREATE TABLE "keterangan_kelas_kata" (
    "key" varchar(255) NOT NULL PRIMARY KEY,
    "deskripsi" text NOT NULL
);

CREATE TABLE "keterangan_kosakata" (
    "key" varchar(255) NOT NULL PRIMARY KEY,
    "deskripsi" text NOT NULL
);

CREATE TABLE "keterangan_contoh" (
    "key" varchar(255) NOT NULL PRIMARY KEY,
    "deskripsi" text NOT NULL
);

CREATE TABLE "keterangan_teks" (
    "key" varchar(255) NOT NULL PRIMARY KEY,
    "deskripsi" text NOT NULL,
    "kategori" text NOT NULL
);

--------- Relasi Antar Tabel

ALTER TABLE "tb_contoh"
    ADD COLUMN "kosakata_id" int NOT NULL
    REFERENCES tb_kosakata(id);

ALTER TABLE "tb_teks"
    ADD COLUMN "contoh_id" int NOT NULL
    REFERENCES tb_contoh(id);

ALTER TABLE "tb_kosakata"
    ADD COLUMN "keterangan" varchar(255)
    REFERENCES keterangan_kosakata(key);

ALTER TABLE "tb_contoh"
    ADD COLUMN "keterangan" varchar(255)
    REFERENCES keterangan_contoh(key);

ALTER TABLE "tb_teks"
    ADD COLUMN "keterangan" varchar(255)
    REFERENCES keterangan_teks(key);

ALTER TABLE "tb_teks"
    ADD COLUMN "kelas_kata" varchar(255)
    REFERENCES keterangan_kelas_kata(key);


--------- Data keterangan

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

--------- View untuk statistik data

-- Jumlah data teks per keterangan
CREATE VIEW "teks_keterangan_count" AS
    SELECT
        tb_teks.keterangan,
        bahasa,
        COUNT(*) AS count
    FROM tb_teks
    JOIN tb_contoh ON
    tb_contoh.id = tb_teks.contoh_id
    GROUP BY tb_teks.keterangan, bahasa;

-- Jumlah data teks per kelas kata
CREATE VIEW "teks_kelas_kata_count" AS
    SELECT
        kelas_kata,
        bahasa,
        COUNT(*) AS count
    FROM tb_teks
    JOIN tb_contoh ON
    tb_contoh.id = tb_teks.contoh_id
    GROUP BY kelas_kata, bahasa;

-- Jumlah data contoh per keterangan
CREATE VIEW "contoh_keterangan_count" AS
    SELECT
        keterangan,
        bahasa,
        COUNT(*) AS count
    FROM tb_contoh
    GROUP BY keterangan, bahasa;

-- Statistik jumlah data
CREATE VIEW "data_count" AS
    SELECT
    (SELECT count(*) from keterangan_kosakata) kk,
    (SELECT count(*) from keterangan_contoh) kc,
    (SELECT count(*) from keterangan_kelas_kata) kkk,
    (SELECT count(*) from keterangan_teks) kt,
    (SELECT count(*) from tb_kosakata) tbk,
    (SELECT count(*) from tb_contoh) tbc,
    (SELECT count(*) from tb_contoh
        WHERE bahasa = 'MAD') tbcm,
    (SELECT count(*) from tb_contoh
        WHERE bahasa = 'IND') tbci,
    (SELECT count(*) from tb_teks) tbt,
    (SELECT count(*) from tb_teks
        JOIN tb_contoh ON
        tb_teks.contoh_id = tb_contoh.id
        WHERE bahasa = 'MAD') tbtm,
    (SELECT count(*) from tb_teks
        JOIN tb_contoh ON
        tb_teks.contoh_id = tb_contoh.id
        WHERE bahasa = 'IND') tbti;


