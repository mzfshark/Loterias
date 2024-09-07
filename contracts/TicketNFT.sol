// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract TicketNFT is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIdCounter;

    // Mapping from token ID to ticket details
    mapping(uint256 => uint8[]) public ticketDetails;

    constructor() ERC721("TicketNFT", "TNFT") {}

    function mint(address to, uint8[] calldata _chosenNumbers) external onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter.current();
        _mint(to, tokenId);
        ticketDetails[tokenId] = _chosenNumbers;
        _tokenIdCounter.increment();
        return tokenId;
    }

    function _baseURI() internal view virtual override returns (string memory) {
        return "https://api.yourdomain.com/metadata/";
    }

    function tokenURI(uint256 tokenId) public view virtual override returns (string memory) {
        require(_exists(tokenId), "ERC721Metadata: URI query for nonexistent token");
        return string(abi.encodePacked(_baseURI(), uint2str(tokenId)));
    }

    function uint2str(uint256 _i) internal pure returns (string memory _uintAsString) {
        if (_i == 0) return "0";
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
}
