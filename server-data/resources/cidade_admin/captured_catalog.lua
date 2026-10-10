-- Shared catalogue helpers; captures retain the original numeric model hash.
CidadeCapturedCatalog={objects={},marks={},revision=-1}
function CidadeCapturedCatalog.merge(data)
    if type(data)~='table' or type(data.objects)~='table' then return false end
    if data.revision==CidadeCapturedCatalog.revision then return false end
    CidadeCapturedCatalog.objects=data.objects;CidadeCapturedCatalog.marks=data.marks or {};CidadeCapturedCatalog.revision=data.revision
    return true
end
function CidadeCapturedCatalog.hash(row)
    return row and row.hash or joaat(row and row.model or '')
end
