CREATE DATABASE IF NOT EXISTS gerenciador_db;
USE gerenciador_db;

CREATE TABLE IF NOT EXISTS tb_usuarios (
    user_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    user_nome VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    user_senha VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_tarefas (
    trf_id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    trf_descricao VARCHAR(255) NOT NULL,
    trf_status VARCHAR(255) NOT NULL,
    trf_data_criacao DATETIME NOT NULL,
    trf_data_limite DATETIME NOT NULL,
    trf_prioridade VARCHAR(255) NOT NULL,
    trf_categoria VARCHAR(255) NOT NULL,
    trf_user_id INT NOT NULL,
    FOREIGN KEY (trf_user_id) REFERENCES tb_usuarios(user_id)
);

select * from tb_usuarios;