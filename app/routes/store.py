from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_

from app.models import (
    URGENCY_SCORE,
    Occurrence,
    OccurrenceMapping,
    OccurrenceStatusHistory,
    Product,
    User,
    db,
)


store_bp = Blueprint("store", __name__)

CART_SESSION_KEY = "cart"
AUTO_COUPON_CODE = "CUIDADO100"
USER_SESSION_KEY = "user_id"

CATEGORY_PAGE_COPY = {
    "kits": {
        "title": "Kits",
        "subtitle": "Combinacoes estrategicas para uma rotina completa",
        "text": (
            "As vezes, um unico cuidado nao basta. Nossos kits reforcam protecao, "
            "conexao e precisao em um fluxo familiar de e-commerce."
        ),
    },
    "skincare": {
        "title": "Skincare",
        "subtitle": "Base de defesa diaria",
        "text": (
            "Antes de qualquer cobertura, existe a integridade da pele. Esta secao "
            "simboliza preparo, barreira e continuidade de cuidado."
        ),
    },
    "maquiagem": {
        "title": "Maquiagem",
        "subtitle": "Expressao com controle e discricao",
        "text": (
            "A vitrine de maquiagem sustenta a camuflagem da interface e permite "
            "navegacao sem sinais explicitos de denuncia."
        ),
    },
}

TESTIMONIALS = [
    {
        "name": "CAROL",
        "photo": "img-clientes1-alomana.jpg",
        "text": "Senti que consegui seguir o fluxo com naturalidade e sem chamar atencao.",
    },
    {
        "name": "ADRIANA",
        "photo": "img-clientes2-alomana.jpg",
        "text": "A linguagem de cuidado foi clara e discreta durante toda a navegacao.",
    },
    {
        "name": "IGOR",
        "photo": "img-clientes3-alomana.jpg",
        "text": "Painel administrativo objetivo para triagem e encaminhamento das ocorrencias.",
    },
    {
        "name": "SELMA",
        "photo": "img-clientes4-alomana.jpg",
        "text": "Checkout sem cobranca e registro rapido foram pontos fortes do prototipo.",
    },
]


def _sanitize_quantity(raw_quantity, default_value=1):
    try:
        qty = int(raw_quantity)
    except (TypeError, ValueError):
        return default_value
    return max(1, min(qty, 99))


def _get_cart_dict():
    raw_cart = session.get(CART_SESSION_KEY, {})
    if not isinstance(raw_cart, dict):
        raw_cart = {}

    cleaned_cart = {}
    for key, value in raw_cart.items():
        try:
            product_id = int(key)
            quantity = int(value)
        except (TypeError, ValueError):
            continue
        if quantity > 0:
            cleaned_cart[str(product_id)] = min(quantity, 99)

    if cleaned_cart != raw_cart:
        session[CART_SESSION_KEY] = cleaned_cart
        session.modified = True
    return cleaned_cart


def _save_cart(cart):
    session[CART_SESSION_KEY] = cart
    session.modified = True


def _build_cart_lines():
    cart = _get_cart_dict()
    if not cart:
        return [], 0

    product_ids = [int(product_id) for product_id in cart.keys()]
    products = Product.query.filter(Product.id.in_(product_ids), Product.active.is_(True)).all()
    products_map = {product.id: product for product in products}

    lines = []
    subtotal_cents = 0
    for product_id_str, quantity in cart.items():
        product = products_map.get(int(product_id_str))
        if not product:
            continue
        line_total_cents = product.price_cents * quantity
        subtotal_cents += line_total_cents
        lines.append(
            {
                "product": product,
                "quantity": quantity,
                "line_total_cents": line_total_cents,
            }
        )
    return lines, subtotal_cents


def _apply_ordering(query, order_code):
    if order_code == "menor-preco":
        return query.order_by(Product.price_cents.asc(), Product.id.asc())
    if order_code == "maior-preco":
        return query.order_by(Product.price_cents.desc(), Product.id.asc())
    return query.order_by(Product.featured_order.asc(), Product.id.asc())


def _load_products(search_term="", category_slug="", order_code="mais-vendidos"):
    query = Product.query.filter(Product.active.is_(True))

    if category_slug and category_slug != "todos":
        query = query.filter(Product.category_slug == category_slug)

    if search_term:
        like_term = f"%{search_term}%"
        query = query.filter(
            or_(
                Product.name.ilike(like_term),
                Product.description_short.ilike(like_term),
                Product.description_long.ilike(like_term),
            )
        )

    query = _apply_ordering(query, order_code)
    return query.all()


def _current_user():
    user_id = session.get(USER_SESSION_KEY)
    if not user_id:
        return None
    return db.session.get(User, user_id)


@store_bp.route("/")
def home_page():
    featured_products = _load_products(order_code="mais-vendidos")[:4]
    return render_template(
        "store/home.html",
        featured_products=featured_products,
        testimonials=TESTIMONIALS,
        active_nav="home",
    )


@store_bp.route("/produtos")
def products_page():
    search_term = request.args.get("q", "").strip()
    category_slug = request.args.get("categoria", "todos").strip().lower() or "todos"
    order_code = request.args.get("ordem", "mais-vendidos").strip().lower() or "mais-vendidos"
    products = _load_products(search_term=search_term, category_slug=category_slug, order_code=order_code)

    return render_template(
        "store/products.html",
        products=products,
        selected_category=category_slug,
        selected_order=order_code,
        search_term=search_term,
        category_copy=CATEGORY_PAGE_COPY.get(category_slug),
        active_nav="produtos" if category_slug == "todos" else category_slug,
    )


@store_bp.route("/categoria/<slug>")
def category_page(slug):
    category_slug = slug.strip().lower()
    if category_slug not in CATEGORY_PAGE_COPY:
        abort(404)

    search_term = request.args.get("q", "").strip()
    order_code = request.args.get("ordem", "mais-vendidos").strip().lower() or "mais-vendidos"
    products = _load_products(search_term=search_term, category_slug=category_slug, order_code=order_code)

    return render_template(
        "store/products.html",
        products=products,
        selected_category=category_slug,
        selected_order=order_code,
        search_term=search_term,
        category_copy=CATEGORY_PAGE_COPY[category_slug],
        active_nav=category_slug,
    )


@store_bp.route("/kits")
def kits_page():
    return redirect(url_for("store.category_page", slug="kits"))


@store_bp.route("/skincare")
def skincare_page():
    return redirect(url_for("store.category_page", slug="skincare"))


@store_bp.route("/maquiagem")
def maquiagem_page():
    return redirect(url_for("store.category_page", slug="maquiagem"))


@store_bp.route("/produto/<slug>")
def product_detail_page(slug):
    product = Product.query.filter_by(slug=slug, active=True).first_or_404()
    related_products = (
        Product.query.filter(
            Product.active.is_(True),
            Product.category_slug == product.category_slug,
            Product.id != product.id,
        )
        .order_by(Product.featured_order.asc(), Product.id.asc())
        .limit(4)
        .all()
    )
    return render_template(
        "store/product_detail.html",
        product=product,
        related_products=related_products,
        active_nav=product.category_slug,
    )


@store_bp.route("/institucional")
def institutional_page():
    return render_template("store/institutional.html", active_nav="institucional")


@store_bp.route("/carrinho")
def cart_page():
    cart_lines, subtotal_cents = _build_cart_lines()
    return render_template(
        "store/cart.html",
        cart_lines=cart_lines,
        subtotal_cents=subtotal_cents,
        active_nav="carrinho",
    )


@store_bp.route("/carrinho/item", methods=["POST"])
def add_cart_item():
    product_id = request.form.get("product_id", type=int)
    quantity = _sanitize_quantity(request.form.get("quantity", 1), default_value=1)
    redirect_to = request.form.get("next") or request.referrer or url_for("store.cart_page")

    product = Product.query.filter_by(id=product_id, active=True).first()
    if not product:
        flash("Produto nao encontrado.", "error")
        return redirect(redirect_to)

    cart = _get_cart_dict()
    current_quantity = cart.get(str(product.id), 0)
    cart[str(product.id)] = min(current_quantity + quantity, 99)
    _save_cart(cart)

    flash("Item adicionado ao carrinho.", "success")
    return redirect(redirect_to)


@store_bp.route("/carrinho/item/<int:item_id>/qtd", methods=["POST"])
def update_cart_item(item_id):
    redirect_to = request.form.get("next") or url_for("store.cart_page")
    cart = _get_cart_dict()
    key = str(item_id)
    if key not in cart:
        flash("Item nao encontrado no carrinho.", "error")
        return redirect(redirect_to)

    quantity = request.form.get("quantity", type=int)
    if quantity is None:
        action = request.form.get("action")
        if action == "inc":
            quantity = cart[key] + 1
        elif action == "dec":
            quantity = cart[key] - 1
        else:
            quantity = cart[key]

    if quantity <= 0:
        cart.pop(key, None)
    else:
        cart[key] = min(quantity, 99)

    _save_cart(cart)
    return redirect(redirect_to)


@store_bp.route("/carrinho/item/<int:item_id>/remover", methods=["POST"])
def remove_cart_item(item_id):
    redirect_to = request.form.get("next") or url_for("store.cart_page")
    cart = _get_cart_dict()
    cart.pop(str(item_id), None)
    _save_cart(cart)
    flash("Item removido do carrinho.", "success")
    return redirect(redirect_to)


@store_bp.route("/checkout")
def checkout_page():
    cart_lines, subtotal_cents = _build_cart_lines()
    if not cart_lines:
        flash("Seu carrinho esta vazio.", "warning")
        return redirect(url_for("store.products_page"))

    user = _current_user()
    if not user:
        flash("Faca login para acompanhar seu pedido.", "warning")
        return redirect(url_for("user.login_page", next=url_for("store.checkout_page")))

    discount_cents = subtotal_cents
    total_cents = 0
    return render_template(
        "store/checkout.html",
        cart_lines=cart_lines,
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
        auto_coupon_code=AUTO_COUPON_CODE,
        user=user,
        active_nav="checkout",
    )


@store_bp.route("/checkout/finalizar", methods=["POST"])
def checkout_finalize():
    cart_lines, subtotal_cents = _build_cart_lines()
    if not cart_lines:
        flash("Seu carrinho esta vazio.", "warning")
        return redirect(url_for("store.products_page"))

    user = _current_user()
    if not user:
        flash("Faca login para concluir e acompanhar seu pedido.", "warning")
        return redirect(url_for("user.login_page", next=url_for("store.checkout_page")))

    observation = (request.form.get("observation") or "").strip() or None
    contact_phone = (request.form.get("contact_phone") or "").strip() or None
    contact_email = (request.form.get("contact_email") or "").strip() or None

    product_ids = [line["product"].id for line in cart_lines]
    mappings = OccurrenceMapping.query.filter(OccurrenceMapping.product_id.in_(product_ids)).all()
    mappings_by_product_id = {mapping.product_id: mapping for mapping in mappings}

    categories = []
    highest_urgency = "Baixa"

    items_snapshot = []
    for line in cart_lines:
        product = line["product"]
        mapping = mappings_by_product_id.get(product.id)
        if mapping:
            categories.append(mapping.occurrence_category)
            mapping_urgency = (
                mapping.urgency_level if mapping.urgency_level in URGENCY_SCORE else "Baixa"
            )
            if URGENCY_SCORE[mapping_urgency] > URGENCY_SCORE[highest_urgency]:
                highest_urgency = mapping_urgency
        else:
            categories.append("Ocorrencia geral")

        items_snapshot.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "category_slug": product.category_slug,
                "quantity": line["quantity"],
                "unit_price_cents": product.price_cents,
                "line_total_cents": line["line_total_cents"],
            }
        )

    mapped_category = ", ".join(list(dict.fromkeys(categories))) or "Ocorrencia geral"
    discount_cents = subtotal_cents
    total_cents = 0

    occurrence = Occurrence(
        status="Novo",
        mapped_category=mapped_category,
        urgency_level=highest_urgency,
        user_id=user.id,
        contact_phone=contact_phone,
        contact_email=contact_email,
        observation=observation,
        subtotal_cents=subtotal_cents,
        discount_cents=discount_cents,
        total_cents=total_cents,
    )
    occurrence.set_items(items_snapshot)
    db.session.add(occurrence)
    db.session.flush()

    db.session.add(
        OccurrenceStatusHistory(
            occurrence_id=occurrence.id,
            previous_status=None,
            new_status="Novo",
            changed_by_admin_id=None,
        )
    )
    db.session.commit()

    _save_cart({})
    flash("Pedido finalizado com sucesso. Protocolo registrado.", "success")
    return redirect(url_for("store.checkout_success_page", occurrence_id=occurrence.id))


@store_bp.route("/checkout/sucesso/<int:occurrence_id>")
def checkout_success_page(occurrence_id):
    occurrence = Occurrence.query.get_or_404(occurrence_id)
    user = _current_user()
    if not user or occurrence.user_id != user.id:
        flash("Acesso permitido apenas ao titular do pedido.", "error")
        return redirect(url_for("user.login_page", next=url_for("user.orders_page")))
    return render_template(
        "store/checkout_success.html",
        occurrence=occurrence,
        user=user,
        active_nav="checkout",
    )
