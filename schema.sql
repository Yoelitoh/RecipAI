CREATE TABLE IF NOT EXISTS ingrediente (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  es_basico BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE KEY uq_ingrediente_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS receta (
  id INT UNSIGNED PRIMARY KEY,
  nombre VARCHAR(200) NOT NULL,
  categoria_original VARCHAR(100) NULL,
  tipo_plato VARCHAR(40) NOT NULL,
  momento VARCHAR(40) NULL,
  pais CHAR(3) NULL,
  duracion_min INT NULL,
  comensales INT NULL,
  dificultad VARCHAR(20) NULL,
  instrucciones MEDIUMTEXT NOT NULL,
  url VARCHAR(255) NULL,
  KEY idx_receta_tipo (tipo_plato)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS receta_ingrediente (
  receta_id INT UNSIGNED NOT NULL,
  ingrediente_id INT UNSIGNED NOT NULL,
  texto_original VARCHAR(500) NULL,
  PRIMARY KEY (receta_id, ingrediente_id),
  KEY idx_ri_ingrediente (ingrediente_id),
  CONSTRAINT fk_ri_receta FOREIGN KEY (receta_id) REFERENCES receta (id) ON DELETE CASCADE,
  CONSTRAINT fk_ri_ingrediente FOREIGN KEY (ingrediente_id) REFERENCES ingrediente (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
