import json
from datetime import datetime

from sqlalchemy import inspect, text
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()

VALID_URGENCY_LEVELS = ("Baixa", "Média", "Alta", "Crítica")
VALID_OCCURRENCE_STATUSES = ("Novo", "Em triagem", "Encaminhado", "Concluído")
URGENCY_SCORE = {"Baixa": 1, "Média": 2, "Alta": 3, "Crítica": 4}


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    category_slug = db.Column(db.String(40), nullable=False, index=True)
    category_label = db.Column(db.String(80), nullable=False)
    price_cents = db.Column(db.Integer, nullable=False)
    description_short = db.Column(db.Text, nullable=False)
    description_long = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    featured_order = db.Column(db.Integer, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)

    mapping = db.relationship(
        "OccurrenceMapping",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    occurrences = db.relationship(
        "Occurrence",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(Occurrence.created_at)",
    )
    messages = db.relationship(
        "OccurrenceUserMessage",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(OccurrenceUserMessage.created_at)",
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class OccurrenceMapping(db.Model):
    __tablename__ = "occurrence_mappings"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, unique=True, index=True
    )
    occurrence_category = db.Column(db.String(120), nullable=False)
    urgency_level = db.Column(db.String(20), nullable=False, default="Baixa")

    product = db.relationship("Product", back_populates="mapping")


class Occurrence(db.Model):
    __tablename__ = "occurrences"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    status = db.Column(db.String(30), nullable=False, default="Novo", index=True)
    mapped_category = db.Column(db.String(255), nullable=False)
    urgency_level = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)

    contact_phone = db.Column(db.String(40), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    observation = db.Column(db.Text, nullable=True)

    items_json = db.Column(db.Text, nullable=False, default="[]")
    subtotal_cents = db.Column(db.Integer, nullable=False, default=0)
    discount_cents = db.Column(db.Integer, nullable=False, default=0)
    total_cents = db.Column(db.Integer, nullable=False, default=0)

    notes = db.relationship(
        "OccurrenceNote",
        back_populates="occurrence",
        cascade="all, delete-orphan",
        order_by="desc(OccurrenceNote.created_at)",
    )
    user_messages = db.relationship(
        "OccurrenceUserMessage",
        back_populates="occurrence",
        cascade="all, delete-orphan",
        order_by="desc(OccurrenceUserMessage.created_at)",
    )
    histories = db.relationship(
        "OccurrenceStatusHistory",
        back_populates="occurrence",
        cascade="all, delete-orphan",
        order_by="desc(OccurrenceStatusHistory.changed_at)",
    )
    user = db.relationship("User", back_populates="occurrences")

    def set_items(self, items):
        self.items_json = json.dumps(items, ensure_ascii=False)

    def get_items(self):
        try:
            return json.loads(self.items_json or "[]")
        except (json.JSONDecodeError, TypeError):
            return []


class OccurrenceNote(db.Model):
    __tablename__ = "occurrence_notes"

    id = db.Column(db.Integer, primary_key=True)
    occurrence_id = db.Column(
        db.Integer, db.ForeignKey("occurrences.id"), nullable=False, index=True
    )
    admin_user_id = db.Column(db.Integer, db.ForeignKey("admin_users.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    note_text = db.Column(db.Text, nullable=False)

    occurrence = db.relationship("Occurrence", back_populates="notes")
    admin_user = db.relationship("AdminUser", back_populates="notes")


class OccurrenceUserMessage(db.Model):
    __tablename__ = "occurrence_user_messages"

    id = db.Column(db.Integer, primary_key=True)
    occurrence_id = db.Column(
        db.Integer, db.ForeignKey("occurrences.id"), nullable=False, index=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    message_text = db.Column(db.Text, nullable=False)

    occurrence = db.relationship("Occurrence", back_populates="user_messages")
    user = db.relationship("User", back_populates="messages")


class OccurrenceStatusHistory(db.Model):
    __tablename__ = "occurrence_status_history"

    id = db.Column(db.Integer, primary_key=True)
    occurrence_id = db.Column(
        db.Integer, db.ForeignKey("occurrences.id"), nullable=False, index=True
    )
    changed_by_admin_id = db.Column(
        db.Integer, db.ForeignKey("admin_users.id"), nullable=True, index=True
    )
    previous_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)
    changed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    occurrence = db.relationship("Occurrence", back_populates="histories")
    changed_by = db.relationship("AdminUser", back_populates="status_changes")


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    notes = db.relationship("OccurrenceNote", back_populates="admin_user")
    status_changes = db.relationship("OccurrenceStatusHistory", back_populates="changed_by")

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


DEFAULT_PRODUCTS = [
    {
        "slug": "corretivo-colorido-4-seasons",
        "name": "Corretivo Colorido | 4 Seasons",
        "category_slug": "maquiagem",
        "category_label": "Maquiagem",
        "price_cents": 5990,
        "description_short": "Alta cobertura para neutralizar marcas e imperfeicoes da pele.",
        "description_long": (
            "Sua pele uniforme novamente. Neutraliza tons indesejados com alta cobertura "
            "e acabamento natural. O cuidado que protege sem chamar atencao."
        ),
        "image_filename": "img-produtos-corretivos-alomana.jpg",
        "featured_order": 1,
    },
    {
        "slug": "base-liquida-second-skin",
        "name": "Base Liquida Fluid | Second Skin",
        "category_slug": "maquiagem",
        "category_label": "Maquiagem",
        "price_cents": 9890,
        "description_short": "Age como uma segunda pele e reforca a protecao diaria.",
        "description_long": (
            "Textura leve, cobertura estrategica e acabamento natural para manter o foco "
            "no que importa com seguranca."
        ),
        "image_filename": "img-produtos-base-alomana.jpg",
        "featured_order": 2,
    },
    {
        "slug": "paleta-behind-the-scenes",
        "name": "Paleta de Sombras | Behind The Scenes",
        "category_slug": "maquiagem",
        "category_label": "Maquiagem",
        "price_cents": 11990,
        "description_short": "Crie profundidade e camadas com tons intensos.",
        "description_long": (
            "Uma paleta versatil para adaptar sua rotina sem expor sua intencao. "
            "Controle total em um fluxo familiar."
        ),
        "image_filename": "img-produtos-paletaDeSombra-alomana.jpg",
        "featured_order": 3,
    },
    {
        "slug": "mascara-speak-volume",
        "name": "Mascara de Cilios | Speak Volume",
        "category_slug": "maquiagem",
        "category_label": "Maquiagem",
        "price_cents": 6490,
        "description_short": "Definicao a prova de emocao e volume ao olhar.",
        "description_long": (
            "Longa duracao e aplicacao precisa. Um item rapido para sinalizar apoio com "
            "discricao."
        ),
        "image_filename": "img-produtos-rimel-alomana.jpg",
        "featured_order": 4,
    },
    {
        "slug": "kit-mae-e-filha",
        "name": "Kit Mae e Filha",
        "category_slug": "kits",
        "category_label": "Kits",
        "price_cents": 14990,
        "description_short": "Combinacao protetora para cuidado em dupla.",
        "description_long": (
            "Kit pensado para representar conexao e suporte. Fluxo discreto para pedido "
            "de ajuda com menos atrito."
        ),
        "image_filename": "img-produtos-alomana.jpg",
        "featured_order": 5,
    },
    {
        "slug": "kit-pinceis-precisao",
        "name": "Kit de Pinceis | Precisao",
        "category_slug": "kits",
        "category_label": "Kits",
        "price_cents": 10990,
        "description_short": "Controle total para uma rotina organizada.",
        "description_long": (
            "Ferramentas essenciais para uma rotina objetiva, com linguagem de cuidado "
            "e protecao."
        ),
        "image_filename": "img-produtos-alomana.jpg",
        "featured_order": 6,
    },
    {
        "slug": "gel-limpeza-purify-reset",
        "name": "Gel de Limpeza | Purify & Reset",
        "category_slug": "skincare",
        "category_label": "Skincare",
        "price_cents": 7990,
        "description_short": "Remove residuos e devolve equilibrio para a pele.",
        "description_long": (
            "Limpeza diaria com foco em restauracao e barreira protetora. Cuidado com "
            "minimizacao de exposicao."
        ),
        "image_filename": "img-produtos-alomana.jpg",
        "featured_order": 7,
    },
    {
        "slug": "protetor-barreira-invisivel",
        "name": "Protetor Solar | Barreira Invisivel",
        "category_slug": "skincare",
        "category_label": "Skincare",
        "price_cents": 8990,
        "description_short": "Defesa diaria contra agentes externos.",
        "description_long": (
            "Formula para manter seguranca e continuidade de uso. Pensado para uso "
            "simples e rapido."
        ),
        "image_filename": "img-produtos-alomana.jpg",
        "featured_order": 8,
    },
]

DEFAULT_PRODUCT_MAPPINGS = {
    "corretivo-colorido-4-seasons": ("Violencia fisica", "Alta"),
    "base-liquida-second-skin": ("Violencia psicologica", "Média"),
    "paleta-behind-the-scenes": ("Assedio", "Média"),
    "mascara-speak-volume": ("Ameaca imediata", "Crítica"),
    "kit-mae-e-filha": ("Risco familiar", "Alta"),
    "kit-pinceis-precisao": ("Violencia patrimonial", "Média"),
    "gel-limpeza-purify-reset": ("Violencia moral", "Baixa"),
    "protetor-barreira-invisivel": ("Acompanhamento continuo", "Baixa"),
}


def seed_database(app_config):
    existing_products = {item.slug: item for item in Product.query.all()}
    created_new_products = False

    for product_data in DEFAULT_PRODUCTS:
        if product_data["slug"] in existing_products:
            continue
        db.session.add(Product(**product_data))
        created_new_products = True

    if created_new_products:
        db.session.commit()

    all_products = {item.slug: item for item in Product.query.all()}

    for slug, product in all_products.items():
        default_category, default_urgency = DEFAULT_PRODUCT_MAPPINGS.get(
            slug, ("Ocorrencia geral", "Baixa")
        )
        mapping = OccurrenceMapping.query.filter_by(product_id=product.id).first()
        if mapping:
            continue
        db.session.add(
            OccurrenceMapping(
                product_id=product.id,
                occurrence_category=default_category,
                urgency_level=default_urgency,
            )
        )

    if not AdminUser.query.first():
        admin_user = AdminUser(username=app_config.get("ADMIN_DEFAULT_USERNAME", "admin"))
        admin_user.set_password(app_config.get("ADMIN_DEFAULT_PASSWORD", "admin123"))
        db.session.add(admin_user)

    if not User.query.first():
        demo_user = User(
            username=app_config.get("USER_DEFAULT_USERNAME", "usuario_demo"),
            email=app_config.get("USER_DEFAULT_EMAIL", "usuario@alomana.local"),
        )
        demo_user.set_password(app_config.get("USER_DEFAULT_PASSWORD", "usuario123"))
        db.session.add(demo_user)

    db.session.commit()


def migrate_schema():
    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()
    if "occurrences" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("occurrences")}
    if "user_id" not in columns:
        db.session.execute(text("ALTER TABLE occurrences ADD COLUMN user_id INTEGER"))
        db.session.commit()
