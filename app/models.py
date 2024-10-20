from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, user_nome, user_email, user_senha):
        self.id = user_id
        self.user_nome = user_nome
        self.user_email = user_email
        self.user_senha = user_senha

    @staticmethod
    def get(user_id):
        from app import get_db_connection
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM tb_usuarios WHERE user_id = %s', (user_id,))
            usuario = cursor.fetchone()
            if usuario:
                return User(usuario['user_id'], usuario['user_nome'], usuario['user_email'], usuario['user_senha'])
        return None