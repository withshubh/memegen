import asyncio
from typing import Iterable

from sanic import Blueprint, response
from sanic_openapi import doc

from .. import settings
from ..helpers import save_image
from ..models import Template
from ..text import encode_slug

# TODO: move these two functions


def get_sample_images(request) -> Iterable[str]:
    for template in Template.objects.filter(valid=True):
        yield template.build_sample_url(request.app)


def get_test_images(request) -> Iterable[str]:
    for key, lines in settings.TEST_IMAGES:
        yield request.app.url_for("images.text", key=key, slug=encode_slug(lines))


async def render_image(key: str, slug: str = "", ext: str = settings.DEFAULT_EXT):
    loop = asyncio.get_event_loop()
    path = await loop.run_in_executor(None, save_image, key, slug, ext)
    return await response.file(path)


blueprint = Blueprint("images", url_prefix="/api/images")


@blueprint.get("/")
async def index(request):
    urls = get_sample_images(request)
    return response.json([{"url": url} for url in urls])


@blueprint.post("/")
@doc.consumes(doc.JsonBody({"key": str, "lines": [str]}), location="body")
async def create(request):
    url = request.app.url_for(
        "images.text",
        key=request.json["key"],
        slug=encode_slug(request.json["lines"]),
        _external=True,
    )
    return response.json({"url": url}, status=201)


@blueprint.get("/<key>.png")
async def blank(request, key):
    return await render_image(key)


@blueprint.get("/<key>.jpg")
async def blank_jpg(request, key):
    return await render_image(key, ext="jpg")


@blueprint.get("/<key>/<slug:path>.png")
async def text(request, key, slug):
    return await render_image(key, slug)


@blueprint.get("/<key>/<slug:path>.jpg")
async def text_jpg(request, key, slug):
    return await render_image(key, slug, ext="jpg")
