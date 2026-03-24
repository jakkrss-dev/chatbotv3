import pypdf

reader = pypdf.PdfReader('uploads/รายงานสรุปคำสั่งคณะ.md.pdf')
for page in reader.pages:
    uris = []
    if "/Annots" in page:
        for annot in page["/Annots"]:
            try:
                annot_obj = annot.get_object()
                if annot_obj.get("/Subtype") == "/Link":
                    if "/A" in annot_obj and "/URI" in annot_obj["/A"]:
                        uri = annot_obj["/A"]["/URI"]
                        uris.append(str(uri))
            except Exception as e:
                pass
    if uris:
        print("Found URIs:", uris)
