"""识别与库存共用的五种果蔬目录。

初始化必须预置这些 SKU，C++/Python 识别只按名称命中同一行，
避免现场再建一个“苹果”导致库存对不上。
"""

from __future__ import annotations

from typing import NamedTuple


class CatalogItem(NamedTuple):
    name: str
    category: str
    shelf_life_days: int
    unit: str


PRODUCE_CATALOG: tuple[CatalogItem, ...] = (
    CatalogItem("苹果", "水果", 14, "个"),
    CatalogItem("香蕉", "水果", 7, "根"),
    CatalogItem("胡萝卜", "蔬菜", 14, "根"),
    CatalogItem("黄瓜", "蔬菜", 7, "根"),
    CatalogItem("橙子", "水果", 14, "个"),
)
