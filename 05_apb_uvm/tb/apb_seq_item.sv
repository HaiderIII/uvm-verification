// ============================================================================
// APB Sequence Item (Transaction)
// ============================================================================
// Représente une transaction APB (lecture ou écriture)
// Hérite de uvm_sequence_item
// ============================================================================

class apb_seq_item extends uvm_sequence_item;

    // =========================================================================
    // Champs de la transaction
    // =========================================================================

    // Direction: 1 = Write, 0 = Read
    rand bit        write;

    // Adresse (alignée sur 4 octets)
    rand bit [7:0]  addr;

    // Données à écrire (ignoré pour les lectures)
    rand bit [31:0] wdata;

    // Données lues (rempli par le driver après lecture)
    bit [31:0]      rdata;

    // Réponse du slave
    bit             slverr;

    // =========================================================================
    // TODO 1: Enregistrement UVM
    // =========================================================================
    // Cette macro enregistre la classe dans la factory UVM
    // Elle permet la création d'objets via: apb_seq_item::type_id::create("name")

    `uvm_object_utils_begin(apb_seq_item)
        `uvm_field_int(write,  UVM_ALL_ON)
        `uvm_field_int(addr,   UVM_ALL_ON)
        `uvm_field_int(wdata,  UVM_ALL_ON)
        `uvm_field_int(rdata,  UVM_ALL_ON)
        `uvm_field_int(slverr, UVM_ALL_ON)
    `uvm_object_utils_end

    // =========================================================================
    // TODO 2: Contraintes de randomisation
    // =========================================================================
    // L'adresse doit être alignée sur 4 octets (bits [1:0] = 0)
    // et dans la plage valide (0x00 à 0x0C)

    constraint addr_aligned_c {
        addr[1:0] == 2'b00;  // Alignement 4 octets
    }

    constraint addr_valid_c {
        addr <= 8'h0C;       // Adresses valides: 0x00, 0x04, 0x08, 0x0C
    }

    // =========================================================================
    // Constructeur
    // =========================================================================
    function new(string name = "apb_seq_item");
        super.new(name);
    endfunction

    // =========================================================================
    // TODO 3: Fonction convert2string pour affichage
    // =========================================================================
    // Cette fonction est appelée par UVM pour afficher la transaction

    virtual function string convert2string();
        return $sformatf("%s addr=0x%02h wdata=0x%08h rdata=0x%08h err=%0d",
                         write ? "WRITE" : "READ",
                         addr, wdata, rdata, slverr);
    endfunction

endclass
