// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol";

contract TicketNFT is ERC721, Ownable, ERC721Burnable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    struct Ticket {
        address player;
        uint8[] chosenNumbers;
        uint256 drawRound; // Store draw round info
    }

    mapping(uint256 => Ticket) private _tickets;

    constructor() ERC721("TicketNFT", "TICKET") {}

    function mint(address to, uint8[] memory _chosenNumbers, uint256 _drawRound) external onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();
        
        _safeMint(to, tokenId);

        _tickets[tokenId] = Ticket({
            player: to,
            chosenNumbers: _chosenNumbers,
            drawRound: _drawRound
        });

        return tokenId;
    }

    function getTicket(uint256 tokenId) external view returns (address player, uint8[] memory chosenNumbers, uint256 drawRound) {
        require(_exists(tokenId), "TicketNFT: query for nonexistent token");

        Ticket memory ticket = _tickets[tokenId];
        return (ticket.player, ticket.chosenNumbers, ticket.drawRound);
    }

    function tokenURI(uint256 tokenId) public view virtual override returns (string memory) {
        require(_exists(tokenId), "TicketNFT: URI query for nonexistent token");

        // Generate the token name as "#123456789"
        string memory tokenName = string(abi.encodePacked("#", uint2str(tokenId)));
        
        // Generate a custom image URL
        string memory imageURL = string(abi.encodePacked("https://example.com/images/", uint2str(tokenId), ".png"));

        // Construct the token metadata
        string memory metadata = string(abi.encodePacked(
            '{"name": "', tokenName, '",',
            '"description": "Ticket NFT for CryptoDraw. Draw round: ', uint2str(_tickets[tokenId].drawRound), '",',
            '"image": "', imageURL, '"}'
        ));

        // Return the metadata URL (using a data URI scheme here for simplicity)
        return string(abi.encodePacked("data:application/json;base64,", base64Encode(bytes(metadata))));
    }

    // Helper function to convert uint to string
    function uint2str(uint256 _i) internal pure returns (string memory _uintAsString) {
        if (_i == 0) {
            return "0";
        }
        uint256 j = _i;
        uint256 length;
        while (j != 0) {
            length++;
            j /= 10;
        }
        bytes memory bstr = new bytes(length);
        uint256 k = length;
        j = _i;
        while (j != 0) {
            bstr[--k] = bytes1(uint8(48 + j % 10));
            j /= 10;
        }
        return string(bstr);
    }

    // Base64 encoding of the JSON metadata
    function base64Encode(bytes memory data) internal pure returns (string memory) {
        string memory TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
        string memory PAD = "=";

        uint256 encodedLen = 4 * ((data.length + 2) / 3);
        bytes memory result = new bytes(encodedLen);

        uint256 i;
        uint256 j;
        for (i = 0; i < data.length; i += 3) {
            uint256 input = uint8(data[i]) << 16;
            if (i + 1 < data.length) {
                input |= uint8(data[i + 1]) << 8;
            }
            if (i + 2 < data.length) {
                input |= uint8(data[i + 2]);
            }

            result[j++] = bytes1(TABLE[(input >> 18) & 0x3F]);
            result[j++] = bytes1(TABLE[(input >> 12) & 0x3F]);
            result[j++] = i + 1 < data.length ? bytes1(TABLE[(input >> 6) & 0x3F]) : bytes1(PAD);
            result[j++] = i + 2 < data.length ? bytes1(TABLE[input & 0x3F]) : bytes1(PAD);
        }

        return string(result);
    }
}
