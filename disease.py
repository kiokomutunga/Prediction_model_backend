from database import disease_collection

sample_data = [

    {
        "name": "Bacterial_spot",
        "scientific_name": "Xanthomonas campestris pv. vesicatoria",
        "symptoms": "Small water-soaked lesions on leaves that turn dark brown or black with yellow halos. Severe infection may cause leaf drop.",
        "causes": "Bacterial infection spread by splashing water, contaminated tools, and infected seeds under warm and humid conditions.",
        "treatment": "Application of copper-based bactericides and removal of infected plant debris.",
        "prevention": "Use certified disease-free seeds, avoid overhead irrigation, and practice crop rotation.",
        "references": [
            "FAO Plant Protection Guide (2022)",
            "Journal of Plant Pathology Research (2021)"
        ]
    },

    {
        "name": "Early_blight",
        "scientific_name": "Alternaria solani",
        "symptoms": "Dark concentric rings forming target-like spots on older leaves, often surrounded by yellowing tissue.",
        "causes": "Fungal pathogen thriving in warm, humid environments and plant stress conditions.",
        "treatment": "Application of fungicides such as chlorothalonil or mancozeb.",
        "prevention": "Crop rotation, removal of infected leaves, and proper plant spacing.",
        "references": [
            "FAO Crop Disease Manual (2022)",
            "Plant Disease Journal (2021)"
        ]
    },

    {
        "name": "Late_blight",
        "scientific_name": "Phytophthora infestans",
        "symptoms": "Large water-soaked lesions that rapidly enlarge, leading to leaf collapse and fruit rot.",
        "causes": "Oomycete pathogen favored by cool, wet conditions.",
        "treatment": "Use of systemic fungicides and copper-based sprays.",
        "prevention": "Plant resistant varieties and ensure proper field drainage.",
        "references": [
            "International Plant Protection Convention Report (2022)"
        ]
    },

    {
        "name": "Leaf_Mold",
        "scientific_name": "Passalora fulva",
        "symptoms": "Yellow patches on upper leaf surfaces and olive-green mold on the underside.",
        "causes": "Fungal infection common in greenhouse conditions with high humidity.",
        "treatment": "Application of appropriate fungicides and improved air circulation.",
        "prevention": "Reduce humidity levels and ensure adequate plant spacing.",
        "references": [
            "Greenhouse Crop Protection Handbook (2021)"
        ]
    },

    {
        "name": "Septoria_leaf_spot",
        "scientific_name": "Septoria lycopersici",
        "symptoms": "Small circular spots with dark borders and light gray centers, typically on lower leaves.",
        "causes": "Fungal infection promoted by wet foliage and poor air circulation.",
        "treatment": "Use of protective fungicides and removal of infected leaves.",
        "prevention": "Crop rotation and avoiding overhead irrigation.",
        "references": [
            "FAO Plant Health Bulletin (2022)"
        ]
    },

    {
        "name": "Spider_mites",
        "scientific_name": "Tetranychus urticae",
        "symptoms": "Yellow speckling on leaves, webbing on undersides, and eventual leaf drying.",
        "causes": "Infestation by microscopic mites in hot and dry conditions.",
        "treatment": "Application of miticides and regular leaf washing.",
        "prevention": "Maintain proper humidity and introduce biological control agents.",
        "references": [
            "Integrated Pest Management Guide (2021)"
        ]
    },

    {
        "name": "Target_Spot",
        "scientific_name": "Corynespora cassiicola",
        "symptoms": "Brown circular lesions with concentric rings on leaves and fruits.",
        "causes": "Fungal pathogen spread through rain splash and contaminated debris.",
        "treatment": "Fungicide application and removal of infected plant material.",
        "prevention": "Proper sanitation and crop rotation practices.",
        "references": [
            "Crop Protection Science Review (2022)"
        ]
    },

    {
        "name": "Tomato_Yellow_Leaf_Curl_Virus",
        "scientific_name": "Tomato yellow leaf curl virus (TYLCV)",
        "symptoms": "Upward curling of leaves, yellowing, and stunted plant growth.",
        "causes": "Viral infection transmitted by whiteflies.",
        "treatment": "No direct cure; control whitefly populations.",
        "prevention": "Use resistant varieties and implement vector management strategies.",
        "references": [
            "International Journal of Virology (2021)"
        ]
    },

    {
        "name": "Tomato_mosaic_virus",
        "scientific_name": "Tomato mosaic virus (ToMV)",
        "symptoms": "Mottled light and dark green patterns on leaves and reduced fruit yield.",
        "causes": "Viral infection spread through contaminated tools and human contact.",
        "treatment": "Remove infected plants and disinfect tools.",
        "prevention": "Use certified seeds and maintain strict field hygiene.",
        "references": [
            "Plant Virology Handbook (2022)"
        ]
    },

    {
        "name": "Healthy",
        "scientific_name": "N/A",
        "symptoms": "Leaves appear uniformly green with no visible lesions or discoloration.",
        "causes": "No infection detected.",
        "treatment": "No treatment required.",
        "prevention": "Maintain proper irrigation, nutrition, and pest monitoring.",
        "references": [
            "General Tomato Cultivation Guide (2022)"
        ]
    }

]

disease_collection.insert_many(sample_data)

print("All disease records inserted successfully.")