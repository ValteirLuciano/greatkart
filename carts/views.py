from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Variation
from .models import Cart, CartItem

# A função _cart_id: Tem a funcionalidade de pegar o id do carrinho
# de compra e criar uma sessão.
# Caso não exista o carrinho de compra, a sessão irá criar.
def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


# A função add_cart: Tem a funcionalidade de adicionar o produto no
# carrinho de compra.
def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)  # get the product
    product_variation = []

    # if: Se requisição for igual a POST. Ele vai pegar o item daquela
    # requisição e atribuir ao parametro key do método POST. É o parametro
    # value que estará a requisição POST.
    if request.method == 'POST':
        for item in request.POST:
            key = item
            value = request.POST[key]

            # Como nosso produto trabalha com variações de cor e tamanho, é preciso pegar
            # o nosso produto e suas variações e adicionar(append) na lista product_variation.
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
            except:
                pass

    # Vai pegar o carrinho usando o cart_id presente na sessão
    try:
        cart = Cart.objects.get(cart_id = _cart_id(request)) #get the cart using the cart_id present in the session
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()

    # Se o carrinho com itens existir, ele vai adicionando a lista ex_var_list.
    # Caso contrário, cria-se um novo carrinho.
    is_cart_item_exists = CartItem.objects.filter(product = product, cart = cart).exists()
    if is_cart_item_exists:
        cart_item = CartItem.objects.filter(product = product, cart = cart)

        # existing_variations -> database
        # current variation -> product_variation
        # item_id -> database
        ex_var_list = []
        id = []
        for item in cart_item:
            existing_variation = item.variations.all()
            ex_var_list.append(list(existing_variation))
            id.append(item.id)

        print(ex_var_list)

        if product_variation in ex_var_list:
            # increase the cart item quantity
            index = ex_var_list.index(product_variation)
            item_id = id[index]
            item = CartItem.objects.get(product=product, id=item_id)
            item.quantity += 1
            item.save()

        else:
            item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if len(product_variation) > 0:
                item.variations.clear()
                item.variations.add(*product_variation)
            item.save()

    else:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart,
        )
        if len(product_variation) > 0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variation)
        cart_item.save()
    return redirect('cart')

# Função para decrementar a quantidade do item no carrinho de compra
def remove_cart(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id = product_id)

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')


# Função para remover o item do carrinho de compra
def remove_cart_item(request, product_id, cart_item_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id = product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
    cart_item.delete()
    return redirect('cart')

# Função cart: Tem a funcionalidade de pegar os itens que estão no carrinho,
# pela _card_id da requisição da sessão do carrinho e fazer os calculos do carrinho.
def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = 0
        grand_total = 0
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_items = CartItem.objects.filter(cart = cart, is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total)
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass #just ignore

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,

    }
    return render(request, 'store/cart.html', context)
