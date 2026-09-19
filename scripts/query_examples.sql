-- El-Relato reference queries

-- John 1:1 word-by-word with Strong and morphology
SELECT position, surface, strongs, lemma, morphology_code, gloss, spanish_translation
FROM token_analysis
WHERE book='John' AND chapter=1 AND verse=1
ORDER BY position;

-- All Gospel occurrences linked to G0746 (ἀρχή)
SELECT book, chapter, verse, position, surface, lemma, gloss
FROM token_analysis
WHERE strongs LIKE 'G0746%'
ORDER BY CASE book WHEN 'Matthew' THEN 1 WHEN 'Mark' THEN 2 WHEN 'Luke' THEN 3 ELSE 4 END,
         chapter, verse, position;

-- Edition-apparatus notes for John 1:18
SELECT raw_note, readings_json
FROM edition_apparatus
WHERE book='John' AND chapter=1 AND verse=18
ORDER BY ordinal;

-- Double-bracketed SBLGNT tokens
SELECT book,chapter,verse,position,surface,strongs,lemma,match_method
FROM token_analysis
WHERE textual_status='double-bracketed'
ORDER BY book,chapter,verse,position;

-- Preserved Gospel facsimiles
SELECT source,label,gospels_json,local_path,sha256,size
FROM facsimiles
ORDER BY source,label;
